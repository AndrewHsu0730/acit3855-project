import connexion
from connexion import NoContent
import uuid
import yaml
import logging.config
from pykafka import KafkaClient
from datetime import datetime
import json


with open("config/receiver/app_conf.yaml", "r") as f:
    app_config = yaml.safe_load(f.read())

with open("config/receiver/log_conf.yaml", "r") as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)


logger = logging.getLogger("basicLogger")


client = KafkaClient(hosts = f"{app_config["events"]["hostname"]}:{app_config["events"]["port"]}")
# topic = client.topics[str.encode(app_config["events"]["topic"])]
topic = client.topics[app_config["events"]["topic"]]
producer = topic.get_sync_producer()


def forward_event(event_type, event_data):
    trace_id = event_data["trace_id"]
    msg = {
        "type": event_type,
        "datetime": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "payload": event_data
    }
    msg_str = json.dumps(msg)
    producer.produce(msg_str.encode("utf-8"))
    logger.info(f"Forwarded {event_type} event to Kafka (trace_id: {trace_id})")
    logger.info(f"Data forwarded: {event_data}")
    return NoContent, 201


def add_workout(body):
    trace_id = str(uuid.uuid4())
    body["trace_id"] = trace_id
    logger.info(f"Received workout event with the trace id of {trace_id}")
    return forward_event("workout", body)


def add_diet(body):
    trace_id = str(uuid.uuid4())
    body["trace_id"] = trace_id
    logger.info(f"Received diet event with the trace id of {trace_id}")
    return forward_event("diet", body)


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("bulkup.yaml", base_path = "/receiver", strict_validation = True, validate_responses = True)


if __name__ == "__main__":
    app.run(port=8080, host="0.0.0.0")