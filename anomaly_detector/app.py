# My anomaly service will detect if there are any workout events with weight_lifted value above 50000.
# It'll also detect if there are any diet events with calorie_intake value more than 10000.

import connexion
import yaml
import logging.config
from pykafka import KafkaClient
import json
import time


with open("config/anomaly_detector/app_conf.yaml", "r") as f:
    app_config = yaml.safe_load(f.read())

with open("config/anomaly_detector/log_conf.yaml", "r") as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)


logger = logging.getLogger("basicLogger")


def update_anomalies():
    start_time = time.time()
    logger.debug("Updating anomalies ...")

    client = KafkaClient(hosts=f"{app_config["events"]["hostname"]}:{app_config["events"]["port"]}")
    topic = client.topics[str.encode(app_config["events"]["topic"])]
    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)

    workout_anomalies = []
    diet_anomalies = []

    for msg in consumer:
        message = msg.value.decode("utf-8")
        data = json.loads(message)

        logger.debug(data)

        if data["type"] == "workout" and data["payload"]["weight_lifted"] > 50000:
            workout_anomalies.append({
                "event_id": data["payload"]["workout_id"],
                "trace_id": data["payload"]["trace_id"],
                "type": "workout",
                "description": f"Value detected: {data["payload"]["weight_lifted"]}, threshold: 50000"
            })
            logger.debug(f"Anomaly detected! Value: {data["payload"]["weight_lifted"]}, Threshold: 50000")

        if data["type"] == "diet" and data["payload"]["calorie_intake"] > 10000:
            diet_anomalies.append({
                "event_id": data["payload"]["diet_id"],
                "trace_id": data["payload"]["trace_id"],
                "type": "diet",
                "description": f"Value detected: {data["payload"]["calorie_intake"]}, threshold: 10000"
            })
            logger.debug(f"Anomaly detected! Value: {data["payload"]["calorie_intake"]}, Threshold: 10000")

    anomalies = {
        "workout_anomalies": workout_anomalies,
        "diet_anomalies": diet_anomalies
    }

    with open(app_config["file_path"], "w") as f:
        json.dump(anomalies, f, indent=4)

    processing_time_ms = int((time.time() - start_time) * 1000)
    logger.info(f"Anomaly detection completed | processing_time_ms = {processing_time_ms}")


def get_anomalies(event_type=None):
    allowed = [None, "workout", "diet"]
    if event_type not in allowed:
        return "Event type is invalid.", 400
    
    with open(app_config["file_path"], "r") as f:
        data = json.load(f)

        if event_type == None:
            logger.debug(f"Data returned: {data}")
            return data
        elif event_type == "workout":
            logger.debug(f"Data returned: {data["anomalies"]["workout_anomalies"]}")
            return data["anomalies"]["workout_anomalies"]
        elif event_type == "diet":
            logger.debug(f"Data returned: {data["anomalies"]["diet_anomalies"]}")
            return data["anomalies"]["diet_anomalies"]


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("anomaly.yaml", base_path = "/anomaly-detector", strict_validation = True, validate_responses = True)


if __name__ == "__main__":
    logger.info("Threshold: weight_lifted in workout events is 50000 and calorie_intake in diet events is 10000.")
    app.run(port=8500, host="0.0.0.0")