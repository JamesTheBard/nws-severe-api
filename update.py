import logging
import re
import threading
import time
from datetime import datetime
from pathlib import Path

import pytz
import requests
import schedule
from box import Box
from dateutil.parser import parse
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from rich.logging import RichHandler

from config import Config
from generate import generate_image, notify_discord_webhook

m = MongoClient(Config.MONGO_URI)
db = m[Config.MONGO_ALERTS_DB]

FORMAT = "%(message)s"
logging.basicConfig(level="INFO", format=FORMAT, datefmt='[%X]', handlers=[RichHandler()])

log = logging.getLogger("rich")

def run_threaded(job_func) -> None:
    """Quick function to pass to scheduler to run everything multithreaded.

    Args:
        job_func (function): The function to send into the thread.
    """
    job_thread = threading.Thread(target=job_func)
    job_thread.start()


def filter_alert(rule_list: list[str], alert: Box) -> bool:
    """Filter events based on regular expressions compared against the properties data.

    Args:
        rule_list (list[str]): A list of rules.
        alert (Box): The NWS API event to process.

    Returns:
        bool: Whether the alert was allowed via the rules.
    """
    results = list()
    for rule in rule_list:
        for attrib, values in rule.items():
            temp_results = list()
            if isinstance(values, str):
                values = [values]
            for value in values:
                result = re.search(value, alert.properties[attrib])
                temp_results.append(bool(result))
            results.append(any(temp_results))
    return all(results)


def get_alerts(initial: bool = False) -> int:
    """Poll the NWS API for all current active alerts.

    Returns:
        int: The number of alerts added to the database.
    """
    url = f"{Config.NWS_API_URL}/alerts/active"
    try:
        r = requests.get(url,
                        headers=Config.NWS_API_HEADERS,
                        params=Config.NWS_API_PARAMS)
    except ConnectionError as e:
        log.warning(f"Unable to connect to the National Weather Service API: {e.strerror}")
        return 0
    
    try:
        data = Box(r.json())
    except requests.exceptions.JSONDecodeError as e:
        log.warning("Could not decode NWS API response.")
        log.warning(f"Error: {e.strerror}")
        return 0
    
    log.debug(f"Pulled {len(data.features)} alerts from the NWS.")
    
    rules = [
        r'Thunderstorm',
        r'Tornado',
        r'Flash Flood',
    ]
    
    new_messages = 0
    for f in data.features:
        if add_record(f) and not initial:
            if filter_alert(Config.FILTER_RULES, f):
                image = generate_image(f)
                if image is None:
                    log.warning(f"Unable to generate image for event: {f.properties.event}")
                    log.warning(f" - ID: {f.id}")
                    log.warning(f" - Area: {f.properties.areaDesc}")
                    continue
                log.info(f'Event: "{f.properties.event}"')
                log.info(f' - Area: {f.properties.areaDesc}')
                log.info(f' - Generating image: "{image}"')
                notify_discord_webhook(f, image=image, webhook_url=Config.DISCORD_WEBHOOK)
            else:
                log.info(f"Skipping generating image for event: {f.properties.event}")
            new_messages += 1

    if not new_messages:
        return 0

    log.info(f"Processed {new_messages} alerts from the NWS.")
    return new_messages


def add_record(feature: Box, generate_image: bool = False) -> bool:
    """Add a feature record from the NWS alerts to the Mongo database.

    Args:
        feature (Box): The record to add to the database.

    Returns:
        bool: Whether the record was added to the database (True) or already in the DB (False)
    """
    now = datetime.now(pytz.UTC)
    if parse(feature.properties['expires']) < now:
        log.debug(f"Skipped record '{feature.id}'.")
        return False

    dt_list = ["sent", "effective", "onset", "expires", "ends"]
    for field in dt_list:
        try:
            feature.properties[field] = parse(feature.properties[field])
        except TypeError:
            if field != "ends":
                return

    feature.properties.description = process_description(feature.properties.description)

    coll = db["test"]
    try:
        coll.insert_one(feature)
    except DuplicateKeyError:
        log.debug(f"Key {feature.id} already present in DB, skipping.")
        return False
    return True

def process_description(desc: str) -> str:
    """Remove all unneeded newlines from the string and replace with spaces.

    Args:
        desc (str): The string to process.

    Returns:
        str: The description with all the single newlines being replaced with spaces.
    """
    return "\n\n".join([i.replace("\n", ' ') for i in desc.split("\n\n")])
        

def clean_records() -> int:
    """Remove all expired alerts from the database.

    Returns:
        int: Number of records removed from the database.
    """
    coll = db["test"]
    now = datetime.now(pytz.UTC)
    query = {"properties.expires": {"$lt": now}}
    results = coll.delete_many(query)
    if results.deleted_count:
        log.info(f"Removed {results.deleted_count} expired alerts.")
    return results.deleted_count


def clean_images(days: int = 7) -> int:
    """Delete all images older than 'days' in the image directory.

    Args:
        days (int): The age of the image to delete in days.

    Returns:
        int: The number of images deleted.
    """
    files = Path(Config.IMAGE_SAVE_PATH).glob('*.png')
    count = 0
    current_time = time.time() - (86400 * days)
    for f in files:
        if f.stat().st_mtime < current_time:
            f.unlink()
            count += 1
    if count:
        log.info(f"Removed {count} stale images.")

    return count


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s',
                        level=logging.INFO)
    
    # Initial DB load
    coll = db["test"]
    coll.create_index("id", unique=True)

    log.info("Populating database.")
    get_alerts(initial=True)
    
    log.info("Cleaning stale watches/warnings.")
    clean_records()

    log.info("Cleaning stale images.")
    clean_images()

    schedule.every(10).seconds.do(run_threaded, get_alerts)
    schedule.every(1).minutes.do(run_threaded, clean_records)
    schedule.every(20).minutes.do(run_threaded, clean_images)

    while True:
        schedule.run_pending()
        time.sleep(1)
