import connexion
import httpx
import time
from datetime import datetime
import json
import yaml
import logging.config


with open("config/consistency_check/log_conf.yaml", "r") as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger("basicLogger")


with open("config/consistency_check/app_conf.yaml", "r") as f:
    app_config = yaml.safe_load(f.read())


def run_consistency_checks():
    start_time = time.time()
    logger.info("Consistency check started")

    processing_ep = app_config["services"]["processing"]
    processing_response = httpx.get(processing_ep)
    processing_data = processing_response.json()
    p_workout_count = processing_data["num_of_workout_events"]
    p_diet_count = processing_data["num_of_diet_events"]

    analyzer_count_ep = app_config["services"]["analyzer"]["count"]
    analyzer_count_response = httpx.get(analyzer_count_ep)
    analyzer_count_data = analyzer_count_response.json()
    a_workout_count = analyzer_count_data["num_of_workout_events"]
    a_diet_count = analyzer_count_data["num_of_diet_events"]

    analyzer_wid_ep = app_config["services"]["analyzer"]["wid"]
    analyzer_wid_response = httpx.get(analyzer_wid_ep)
    analyzer_wid = analyzer_wid_response.json()
    logger.debug(f"analyzer_wid: {analyzer_wid}")

    analyzer_did_ep = app_config["services"]["analyzer"]["did"]
    analyzer_did_response = httpx.get(analyzer_did_ep)
    analyzer_did = analyzer_did_response.json()

    storage_count_ep = app_config["services"]["storage"]["count"]
    storage_count_response = httpx.get(storage_count_ep)
    storage_count_data = storage_count_response.json()
    s_workout_count = storage_count_data["workout_row_count"]
    s_diet_count = storage_count_data["diet_row_count"]

    storage_wid_ep = app_config["services"]["storage"]["wid"]
    storage_wid_response = httpx.get(storage_wid_ep)
    storage_wid = storage_wid_response.json()

    storage_did_ep = app_config["services"]["storage"]["did"]
    storage_did_response = httpx.get(storage_did_ep)
    storage_did = storage_did_response.json()

    analyzer_wid_dict = {event["trace_id"]: event["event_id"] for event in analyzer_wid}
    storage_wid_dict = {event["trace_id"]: event["event_id"] for event in storage_wid}
    analyzer_did_dict = {event["trace_id"]: event["event_id"] for event in analyzer_did}
    storage_did_dict = {event["trace_id"]: event["event_id"] for event in storage_did}

    missing_in_db = []
    for trace_id, event_id in analyzer_wid_dict.items():
        if trace_id not in storage_wid_dict:
            missing_in_db.append({
                "event_id": event_id,
                "trace_id": trace_id,
                "type": "workout"
            })

    for trace_id, event_id in analyzer_did_dict.items():
        if trace_id not in storage_did_dict:
            missing_in_db.append({
                "event_id": event_id,
                "trace_id": trace_id,
                "type": "diet"
            })

    missing_in_queue = []
    for trace_id, event_id in storage_wid_dict.items():
        if trace_id not in analyzer_wid_dict:
            missing_in_queue.append({
                "event_id": event_id,
                "trace_id": trace_id,
                "type": "workout"
            })

    for trace_id, event_id in storage_did_dict.items():
        if trace_id not in analyzer_did_dict:
            missing_in_queue.append({
                "event_id": event_id,
                "trace_id": trace_id,
                "type": "diet"
            })

    last_updated = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    data = {
        "last_updated": last_updated,
        "counts": {
            "db": {
                "workout_event": s_workout_count,
                "diet_event": s_diet_count
            },
            "queue": {
                "workout_event": a_workout_count,
                "diet_event": a_diet_count
            },
            "processing": {
                "workout_event": p_workout_count,
                "diet_event": p_diet_count
            }
        },
        "missing_in_db": missing_in_db,
        "missing_in_queue": missing_in_queue
    }

    with open(app_config["file_path"], "w") as f:
        json.dump(data, f, indent=4)

    processing_time_ms = int((time.time() - start_time) * 1000)
    logger.info(f"Consistency check completed | processing_time_ms = {processing_time_ms} | missing_in_db = {len(missing_in_db)} | missing_in_queue = {len(missing_in_queue)}")

    return processing_time_ms


def get_checks():
    try:
        with open(app_config["file_path"], "r") as f:
            data = json.load(f)
    except:
        return "No checks have been run yet", 404
    
    return data


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("consistency_check.yaml", base_path = "/consistency-check", strict_validation = True, validate_responses = True)


if __name__ == "__main__":
    app.run(port=8300, host="0.0.0.0")