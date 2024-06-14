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
    NWS_API_SEVERITY = ["Extreme", "Severe"]
    NWS_API_PARAMS = {
        "severity": ','.join(NWS_API_SEVERITY),
    }

    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://root:root@localhost:27017")
    MONGO_ALERTS_DB = os.environ.get("MONGO_ALERTS_DB", "alerts")
    DISCORD_WEBHOOK = 'https://discord.com/api/webhooks/123456789012345/XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
    IMAGE_SERVER_URL = 'https://put.your.images.here.url'
    IMAGE_SAVE_PATH = "images"

    MAPBOX_PROVIDER = cx.providers.MapBox(accessToken=os.environ.get('MAPBOX_TOKEN', MAPBOX_TOKEN))
    MAPBOX_ZOOM = 9

    # Alert filter
    # [{"properties_attribute": ["regex1", "regex2", ...]}]
    FILTER_RULES = [
        {"event": ["Tornado", "Thunderstorm", "Flash Flood"]}
    ]
    
    # Alert colors
    # Format: {"Event Regex": [0xWATCH_COLOR, 0xWARNING_COLOR]}
    # Should add a color for a given event from the FILTER_RULES otherwise it will default to
    # the ALERT_COLOR_DEFAULT

    ALERT_COLORS = {                          # Watch        Warning
        "Tornado":      [0xc60101, 0xff00ff], # Red          Pink
        "Thunderstorm": [0xe8e800, 0xe89804], # Yellow       Orange
        "Flash Flood":  [0x03c03c, 0x028228], # Light Green  Green   
        "Winter Storm": [0x435882, 0x2360db], # Desat Blue   Bright Blue
    }

    # Alert color for expired alerts
    ALERT_COLOR_EXPIRED = 0x505050 # Gray

    # Alert colors for undefined/unmatched alerts
    ALERT_COLOR_DEFAULT = 0xffffff # White