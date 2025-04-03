import connexion
import yaml
import logging.config
from apscheduler.schedulers.background import BackgroundScheduler
import json
from datetime import datetime
import httpx
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware
import os


with open("config/processing/log_conf.yaml", "r") as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)


logger = logging.getLogger("basicLogger")


with open("config/processing/app_conf.yaml", "r") as f:
    app_config = yaml.safe_load(f.read())


def get_stats():
    logger.info("GET request received for stats")
    try:
        with open("data/processing/stats.json", "r") as f:
            stats = json.load(f)
        logger.debug(f"Stats: {stats}")
        logger.info("GET request for stats completed successfully")
        return stats, 200
    except FileNotFoundError:
        logger.error("Stats file not found")
        return "Statistics do not exist", 404


def populate_stats():
    logger.info("Periodic processing started")

    try:
        with open("data/processing/stats.json", "r") as f:
            stats = json.load(f)
    except FileNotFoundError:
        stats = {
            "num_of_workout_events": 0,
            "max_weight_lifted": 0,
            "num_of_diet_events": 0,
            "max_calorie_intake": 0,
            "last_updated": "2025-01-01T00:00:00Z"
        }
        with open("data/processing/stats.json", "w") as f:
            json.dump(stats, f, indent = 4)
        logger.info("File not found. Created one with default values")
        return 

    current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    workout_endpoint_start = app_config["events"]["workout"]["url"]
    diet_endpoint_start = app_config["events"]["diet"]["url"]
    query = f"?start_timestamp={stats["last_updated"]}&end_timestamp={current_time}"

    workout_endpoint = f"{workout_endpoint_start}{query}"
    diet_endpoint = f"{diet_endpoint_start}{query}"

    workout_response = httpx.get(workout_endpoint)
    diet_response = httpx.get(diet_endpoint)

    if workout_response.status_code != 200:
        logger.error(f"Failed to fetch workout events. Status code: {workout_response.status_code}")
        return 
    if diet_response.status_code != 200:
        logger.error(f"Failed to fetch diet events. Status code: {diet_response.status_code}")
        return 

    workout_events = workout_response.json()
    diet_events = diet_response.json()
    
    logger.info(f"{len(workout_events)} new workout events received")
    logger.info(f"{len(diet_events)} new diet events received")

    stats["num_of_workout_events"] += len(workout_events)
    stats["num_of_diet_events"] += len(diet_events)

    if workout_events:
        max_weight_lifted = max(event["weight_lifted"] for event in workout_events)
        stats["max_weight_lifted"] = max(stats["max_weight_lifted"], max_weight_lifted)
    if diet_events:
        max_calorie_intake = max(event["calorie_intake"] for event in diet_events)
        stats["max_calorie_intake"] = max(stats["max_calorie_intake"], max_calorie_intake)

    stats["last_updated"] = current_time

    with open("data/processing/stats.json", "w") as f:
        json.dump(stats, f, indent = 4)

    logger.debug(f"Updated stats: {json.dumps(stats, indent = 4)}")
    logger.info("Periodic processing ended successfully")


def init_scheduler():
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(populate_stats, 
                  'interval', 
                  seconds=app_config['scheduler']['interval'])
    sched.start()


app = connexion.FlaskApp(__name__, specification_dir='')

if "CORS_ALLOW_ALL" in os.environ and os.environ["CORS_ALLOW_ALL"] == "yes":
    app.add_middleware(
        CORSMiddleware,
        position=MiddlewarePosition.BEFORE_EXCEPTION,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )


app.add_api("bulkup.yaml", base_path = "/processing", strict_validation = True, validate_responses = True)


if __name__ == "__main__":
    init_scheduler()
    app.run(port=8100, host="0.0.0.0")