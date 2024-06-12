from uuid import uuid4
import time
import json

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.io.shapereader as shapereader
import contextily as cx
import logging
import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt
import requests
from box import Box
from shapely import Polygon
from typing import Optional, Union

from config import Config

# We don't need an interactive backend, so we will use 'agg'.
matplotlib.use('agg')

# Load the NWS county definitions.  These are needed for watches as they aren't defined
# by polygons directly in the message.
gpf_counties = gpd.read_file("data/c_05mr24.zip")

# Load the county shapes to draw the county lines on the generated map.
reader = shapereader.Reader("data/countyl010g.shp")
counties = list(reader.geometries())
COUNTIES = cfeature.ShapelyFeature(counties, ccrs.PlateCarree())


class Bounds:
    """A boundary object that contains the outer-most latitude/longitude measurements.

    Attributes:
        north (float): The northern-most latitude.
        south (float): The southern-most latitude.
        east (float): The eastern-most longitude.
        west (float): The western-most longitude.
    """
    north: float
    south: float
    east: float
    west: float

    def __init__(self, north: float = 0., south: float = 0., east: float = 0., west: float = 0.):
        """Create a Bounds object.

        Args:
            north (float, optional): The northern most boundary. Defaults to 0.0.
            south (float, optional): The southern most boundary. Defaults to 0.0.
            east (float, optional): The eastern most boundary. Defaults to 0.0.
            west (float, optional): The western most boundary. Defaults to 0.0.
        """
        self.north = north
        self.south = south
        self.east = east
        self.west = west

    def generate_bounds(self, alert: Union[dict, Box]) -> None:
        """Generate the bounds of the alert polygon(s) from a given NWS alert.

        Args:
            alert (Box): The alert from the NWS service.
        """
        alert = Box(alert)
        lat, lon = list(), list()
        if alert.geometry == None:
            counties = [i[1:] for i in alert.properties.geocode.SAME]
            c = tuple(
                gpf_counties[gpf_counties['FIPS'].isin(counties)].total_bounds)
            self.north = max([c[1], c[3]])
            self.south = min([c[1], c[3]])
            self.east = max(c[0], c[2])
            self.west = min(c[0], c[2])
        else:
            for coordinates in alert.geometry.coordinates:
                for coordinate in coordinates:
                    lat.append(coordinate[1])
                    lon.append(coordinate[0])
            self.north = max(lat)
            self.south = min(lat)
            self.east = max(lon)
            self.west = min(lon)

    @property
    def lat_center(self) -> float:
        """Return the bounding box's latitude center.

        Returns:
            float: The latitude center.
        """
        return (self.north + self.south) / 2

    @property
    def lon_center(self) -> float:
        """Return the bounding box's longitude center.

        Returns:
            float: The longitude center.
        """
        return (self.east + self.west) / 2

    def zoom(self, zoom: float) -> None:
        """Adjust the zoom value of the bounding box.

        Args:
            zoom (float): The zoom level to use to adjust the bounding box.  Values below 1 zoom out, above 1 zoom in.
        """
        lat_adjust = abs(self.north - self.south) / zoom / 2
        lon_adjust = abs(self.east - self.west) / zoom / 2

        lat_center = self.lat_center
        lon_center = self.lon_center

        self.north = lat_center + lat_adjust
        self.south = lat_center - lat_adjust
        self.east = lon_center + lon_adjust
        self.west = lon_center - lon_adjust

    def set_aspect(self, ratio: float) -> None:
        """Change the bounding box aspect ratio.  This only works with PlateCarree coordinate system.

        Args:
            ratio (float): The aspect ratio to use.
        """
        lat_range = abs(self.north - self.south)
        lon_range = abs(self.east - self.west)

        lat_center = self.lat_center
        lon_center = self.lon_center

        current_ratio = lon_range / lat_range
        if current_ratio >= ratio:
            lat_adjust = (lon_range / ratio / 2)
            self.north = lat_center + lat_adjust
            self.south = lat_center - lat_adjust
        else:
            lon_adjust = (lat_range * ratio / 2)
            self.west = lon_center - lon_adjust
            self.east = lon_center + lon_adjust

    def get_lons(self) -> list[float]:
        """Get all of the longitude values for a bounding box.

        Returns:
            list(float): The five longitude values (first and last value are the same).
        """
        return [self.east, self.west, self.west, self.east, self.east]

    def get_lats(self) -> list[float]:
        """Get all of the latitude values for a bounding box.

        Returns:
            float: The five latitude values (first and last value are the same).
        """
        return [self.north, self.north, self.south, self.south, self.north]

    @property
    def bounds(self) -> list[float]:
        """Return the bounds of the bounding box in a format for `ax.set_extent`

        Returns:
            list[float]: The list of bounds in the order of west, east, south, and north.
        """
        return [self.west, self.east, self.south, self.north]

    @property
    def valid(self) -> bool:
        """Returns whether the bounding box is valid or not.

        Returns:
            bool: Returns True if the bounding box is valid.
        """
        return all(i == i for i in self.bounds)

    def __str__(self) -> str:
        return f'<Bounds(north={self.north:.3f}, south={self.south:.3f}, east={self.east:.3f}, west={self.west:.3f})>'


def generate_image(alert: Union[dict, Box]) -> Optional[str]:
    """Generate an image containing the polygon(s) in the NWS alert message.

    Args:
        alert (Box): The NWS alert message.

    Returns:
        Optional[str]: Returns the filename of the image generated from the alert message, or None if unable to render the image.
    """
    alert = Box(alert)
    fig, ax = plt.subplots(subplot_kw=dict(projection=ccrs.Mercator()))
    fig.set_size_inches(16, 9)
    plt.subplots_adjust(left=0, right=1, bottom=0, top=1)

    bounds = Bounds()
    bounds.generate_bounds(alert=alert)

    if not bounds.valid:
        return None

    bounds.zoom(0.7)
    ax.set_extent(bounds.bounds)

    if alert.geometry:
        poly = Polygon(alert.geometry.coordinates[0])
        ax.add_geometries(
            [poly], 
            crs=ccrs.PlateCarree(),
            fc='red', 
            alpha=0.3, 
            ec='red', 
            linewidth=2
        )
    else:
        counties = [i[1:] for i in alert.properties.geocode.SAME]
        counties = gpf_counties[gpf_counties['FIPS'].isin(counties)]
        for _, c in counties.iterrows():
            geometry = c.geometry if isinstance(c.geometry, list) else [c.geometry]
            ax.add_geometries(
                geometry,
                crs=ccrs.PlateCarree(),
                fc='red',
                ec='red',
                alpha=0.3,
                linewidth=2,
            )

    ax.add_feature(COUNTIES, facecolor='none', edgecolor='gray', alpha=0.2)
    cx.add_basemap(
        ax=ax,
        crs=ccrs.Mercator(),
        source=Config.MAPBOX_PROVIDER,
        zoom=Config.MAPBOX_ZOOM,
    )

    plt.axis('off')
    file_name = f"{str(uuid4())}.png"
    plt.savefig(f"{Config.IMAGE_SAVE_PATH}" + "/" +
                file_name, dpi=100, bbox_inches='tight')

    plt.close()

    return file_name


def get_color_from_event(alert: Union[dict, Box]) -> int:
    """Return the color for the associated event as defined in the configuration file.

    Args:
        alert (Union[dict, Box]): The NWS API alert.

    Returns:
        int: The color code associated with the event.
    """
    alert = Box(alert)
    for wtype, colors in Config.ALERT_COLORS.items():
        if wtype in alert.properties.event:
            return colors[0] if "Watch" in alert.properties.event else colors[1]

    if alert.properties.instruction == None:
        return Config.ALERT_COLOR_EXPIRED
    
    return Config.ALERT_COLOR_DEFAULT


def notify_discord_webhook(alert: Union[dict, Box], image: str, webhook_url: str) -> int:
    """Notify a Discord channel via webhook.

    Args:
        alert (Union[dict, Box]): The NWS alert.
        image (str): The name to the rendered image.
        webhook_url (str): The Discord webhook to use.

    Returns:
        int: The status code returned from calling the Discord webhook.
    """
    alert = Box(alert)

    title = alert.properties.event.upper()
    if alert.properties.messageType.lower() == "update":
        title += " (UPDATE)"

    color = get_color_from_event(alert)
    if alert.properties.instruction == None:
        color = 0x1e90ff

    description = alert.properties.description
    if len(description) > 1010:
        description = description[:1007]
        if description[-1] in ' \\':
            description = description[:-1]
        description = description + "..."
    
    description = f"```\n{description}\n```"

    content = {
        'embeds': [
            {
                "title": title,
                "description": f"## {alert.properties.headline}",
                "url": alert.id,
                "color": color,
                "timestamp": alert.properties.effective.isoformat(),
                "image": {
                    "url": Config.IMAGE_SERVER_URL + '/' + image,
                },
                "author": {
                    "name": "National Weather Service",
                    "url": "https://www.spc.noaa.gov"
                },
                "fields": [
                    {
                        "name": "Affected Counties",
                        "value": alert.properties.areaDesc,
                    },
                    {
                        "name": "More Information",
                        "value": description,
                    }
                ]
            }
        ]
    }

    for i in range(3):
        r = requests.post(webhook_url, json=content)
        if r.status_code != 204:
            logging.info(f"Could not trigger webhook, status code '{r.status_code}', retrying.")
            time.sleep(2)
        else:
            logging.info(f"Webhook triggered, return code: {r.status_code}")
            return r.status_code

    logging.warn(f"Failed to send Discord webhook! Response: {r.content.decode()}")
    error_file = f"error_{str(uuid4())}.txt"
    with open(error_file, "w") as f:
        f.write(json.dumps(content))
        
    logging.warn(f'Embed content saved as "{error_file}"')
    return r.status_code
