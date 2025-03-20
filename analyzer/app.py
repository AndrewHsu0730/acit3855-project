import connexion
import yaml
import logging.config
from pykafka import KafkaClient
import json


with open("config/analyzer/app_conf.yaml", "r") as f:
    app_config = yaml.safe_load(f.read())

with open("config/analyzer/log_conf.yaml", "r") as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)


logger = logging.getLogger("basicLogger")


def get_workout_msg(index):
    client = KafkaClient(hosts=f"{app_config["events"]["hostname"]}:{app_config["events"]["port"]}")
    topic = client.topics[str.encode(app_config["events"]["topic"])]
    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)

    counter = 0
    for msg in consumer:
        message = msg.value.decode("utf-8")
        data = json.loads(message)
        logger.debug(data)
        if data["type"] != "workout":
            continue
        if counter == index:
            logger.info(f"Workout message at index {index}: {data}")
            return data, 200
        counter += 1

    logger.error(f"No workout message found at index {index}")
    return {"message": f"No workout message found at index {index}!"}, 404
    # return {"counter": counter}, 200


def get_diet_msg(index):
    client = KafkaClient(hosts=f"{app_config["events"]["hostname"]}:{app_config["events"]["port"]}")
    topic = client.topics[str.encode(app_config["events"]["topic"])]
    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)

    counter = 0
    for msg in consumer:
        message = msg.value.decode("utf-8")
        data = json.loads(message)
        logger.debug(data)
        if data["type"] != "diet":
            continue
        if counter == index:
            logger.info(f"Diet message at index {index}: {data}")
            return data, 200
        counter += 1

    logger.error(f"No diet message found at index {index}")
    return {"message": f"No diet message found at index {index}!"}, 404


def get_stats():
    client = KafkaClient(hosts=f"{app_config["events"]["hostname"]}:{app_config["events"]["port"]}")
    topic = client.topics[str.encode(app_config["events"]["topic"])]
    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)

    num_of_workout_events = 0
    num_of_diet_events = 0

    for msg in consumer:
        message = msg.value.decode("utf-8")
        data = json.loads(message)

        if data["type"] == "workout":
            num_of_workout_events += 1
        elif data["type"] == "diet":
            num_of_diet_events += 1

    return {"num_of_workout_events": num_of_workout_events, "num_of_diet_events": num_of_diet_events}, 200


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("bulkup.yaml", strict_validation = True, validate_responses = True)


if __name__ == "__main__":
    app.run(port=8200, host="0.0.0.0")