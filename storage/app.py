import connexion
from connexion import NoContent
from datetime import datetime
from db_config import make_session
from model import Workout, Diet
import functools
import yaml
import logging.config
from sqlalchemy import select, func
from pykafka import KafkaClient
from pykafka.common import OffsetType
import json
from threading import Thread
from table_create import create_tables


with open("config/storage/app_conf.yaml", "r") as f:
    app_config = yaml.safe_load(f.read())


with open("config/storage/log_conf.yaml", "r") as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)


logger = logging.getLogger("basicLogger")


def process_messages():
    hostname = f"{app_config["events"]["hostname"]}:{app_config["events"]["port"]}"
    client = KafkaClient(hosts = hostname)
    topic = client.topics[str.encode(app_config["events"]["topic"])]

    consumer = topic.get_simple_consumer(
        consumer_group = b"event_group",
        reset_offset_on_start = False,
        auto_offset_reset = OffsetType.LATEST
    )

    for msg in consumer:
        msg_str = msg.value.decode("utf-8")
        msg_json = json.loads(msg_str)
        logger.info("Message: %s" % msg_json)

        payload = msg_json["payload"]

        if msg_json["type"] == "workout":
            add_workout(payload)
        elif msg_json["type"] == "diet":
            add_diet(payload)

        consumer.commit_offsets()


def use_db_session(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        session = make_session()
        trace_id = kwargs.get("body", {}).get("trace_id")
        event_name = func.__name__[4:]
        try:
            return func(session, *args, **kwargs)
        except Exception as e:
            session.rollback()
            print(f"Error adding data to database: {e}")
            return {"message": "Failed to add data"}, 500
        finally:
            session.close()
            logger.info(f"Stored {event_name} event with a trace id of {trace_id}")
    return wrapper


@use_db_session
def add_workout(session, body):
    event = Workout(
        workout_id = body["workout_id"],
        weight_lifted = body["weight_lifted"],
        duration = body["duration"],
        timestamp = datetime.strptime(body["timestamp"], "%Y-%m-%dT%H:%M:%SZ"),
        trace_id = body["trace_id"]
    )
    session.add(event)
    session.commit()
    return NoContent, 201


@use_db_session
def add_diet(session, body):
    event = Diet(
        diet_id = body["diet_id"],
        carb = body["carb"],
        protein = body["protein"],
        veg = body["veg"],
        calorie_intake = body["calorie_intake"],
        timestamp = datetime.strptime(body["timestamp"], "%Y-%m-%dT%H:%M:%SZ"),
        trace_id = body["trace_id"]
    )
    session.add(event)
    session.commit()
    return NoContent, 201


def get_workout_data(start_timestamp, end_timestamp):
    session = make_session()

    start = datetime.strptime(start_timestamp, "%Y-%m-%dT%H:%M:%SZ")
    end = datetime.strptime(end_timestamp, "%Y-%m-%dT%H:%M:%SZ")

    stmt = select(Workout).where(Workout.date_created >= start).where(Workout.date_created < end)

    results = [
        result.to_dict() for result in session.execute(stmt).scalars().all()
    ]

    session.close()

    logger.info("Found %d workout events (start: %s, end: %s)", len(results), start, end)

    return results


def get_diet_data(start_timestamp, end_timestamp):
    session = make_session()

    start = datetime.strptime(start_timestamp, "%Y-%m-%dT%H:%M:%SZ")
    end = datetime.strptime(end_timestamp, "%Y-%m-%dT%H:%M:%SZ")

    stmt = select(Diet).where(Diet.date_created >= start).where(Diet.date_created < end)

    results = [
        result.to_dict() for result in session.execute(stmt).scalars().all()
    ]

    session.close()

    logger.info("Found %d diet events (start: %s, end: %s)", len(results), start, end)

    return results


def count_records():
    session = make_session()

    workout_stmt = select(func.count()).select_from(Workout)
    diet_stmt = select(func.count()).select_from(Diet)

    workout_row_count = session.execute(workout_stmt).scalar()
    diet_row_count = session.execute(diet_stmt).scalar()

    result = {
        "workout_row_count": workout_row_count, 
        "diet_row_count": diet_row_count
    }

    session.close()

    return result


def get_workout_ids():
    session = make_session()

    stmt = select(Workout.workout_id, Workout.trace_id)

    # results = [
    #     result.to_dict() for result in session.execute(stmt).scalars().all()
    # ]

    results = [
        {"event_id": row[0], "trace_id": row[1]}
        for row in session.execute(stmt).all() # try only the all method on multiple cols
    ]

    session.close()

    logger.debug(f"Workout IDs: {results}")

    return results


def get_diet_ids():
    session = make_session()

    stmt = select(Diet.diet_id, Diet.trace_id)

    results = [
        result.to_dict() for result in session.execute(stmt).scalars().all()
    ]

    session.close()

    return results


def setup_kafka_thread():
    t1 = Thread(target=process_messages)
    t1.setDaemon(True)
    t1.start()


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("bulkup.yaml", base_path = "/storage", strict_validation = True, validate_responses = True)


if __name__ == "__main__":
    create_tables()
    setup_kafka_thread()
    app.run(port=8090, host="0.0.0.0")