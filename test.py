from generate import env
import json
import requests
from config import Config

template = env.get_template("embeds_01.j2")
content = template.render(
    title="SEVERE THUNDERSTORM WARNING",
    headline="Severe Thunderstorm Warning issued June 15 at 12:21PM MDT until June 15 at 12:45PM MDT by NWS Great Falls MT",
    url="",
    color=0xffffff,
    timestamp="2024-06-15T12:21:00-06:00",
    map_url="https://wx.jamesthebard.net/fc6f6f22-9198-42bd-a779-7695dd6d8a67.png",
    counties="Cascade, MT; Chouteau, MT",
    description="```\nSVRTFX\n\nThe National Weather Service in Great Falls has issued a\n\n* Severe Thunderstorm Warning for... Southwestern Chouteau County in north central Montana... Northern Cascade County in central Montana...\n\n* Until 1245 PM MDT.\n\n* At 1220 PM MDT, a severe thunderstorm was located near Cascade, moving northeast at 35 mph.\n\nHAZARD...60 mph wind gusts.\n\nSOURCE...Radar indicated.\n\nIMPACT...Expect damage to roofs, siding, and trees.\n\n* Locations impacted include... Great Falls, Cascade, Black Eagle, Tower Rock State Park, Ulm, Malmstrom Afb, Sand Coulee, Tracy, Vaughn, First Peoples Buffalo Jump State Park, and Centerville.\n```",
    # description="",
)
content=json.loads(content, strict=False)
print(content)

r = requests.post(Config.DISCORD_WEBHOOK, json=content)
print(r.status_code, r.content.decode())
