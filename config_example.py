import os
import contextily as cx

MAPBOX_TOKEN = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'

class Config:
    REDIS_URI = os.environ.get("REDIS_URI", "redis://localhost:6379")
    NWS_API_URL = r'https://api.weather.gov'
    NWS_API_HEADERS = {
        "User-Agent": "username@youremail.com",
        "From": "Hugh Mann <username@youremail.com>",
    }
    NWS_API_PARAMS = {
        "severity": ["Extreme", "Severe"],
    }
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://root:root@localhost:27017")
    MONGO_ALERTS_DB = os.environ.get("MONGO_ALERTS_DB", "alerts")
    DISCORD_WEBHOOK = 'https://discord.com/api/webhooks/123456789012345/XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
    IMAGE_SERVER_URL = 'https://put.your.images.here.url'
    IMAGE_SAVE_PATH = "images"

    MAPBOX_PROVIDER = cx.providers.MapBox(accessToken=os.environ.get('MAPBOX_TOKEN', MAPBOX_TOKEN))
    MAPBOX_ZOOM = 9

    FILTER_RULES = [
        {"event": ["Tornado", "Thunderstorm", "Flash Flood"]}
    ]
    
    ALERT_COLORS = {
        "Tornado": [0xff00ff, 0xff00ff],
        "Thunderstorm": [0xffa500, 0xff0000],
        "Flash Flood": [0x03c03c, 0x8fd400],
    }
    ALERT_COLOR_EXPIRED = 0x4169e1
    ALERT_COLOR_DEFAULT = 0xffffff
    