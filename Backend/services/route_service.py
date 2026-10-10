import os
import pandas as pd
import requests


# ==========================================
# PATH
# ==========================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATASET_PATH = os.path.join(
    BASE_DIR,
    "..",
    "data",
    "Synthetic_Dataset.csv"
)


# ==========================================
# LOAD DATASET
# ==========================================

df = pd.read_csv(DATASET_PATH)


# ==========================================
# GET LOCATION COORDINATES
# ==========================================

def get_location_coordinates(location):

    # Check source
    source = df[df["Source"] == location]

    if not source.empty:

        row = source.iloc[0]

        return (
            float(row["Source_Lat"]),
            float(row["Source_Lon"])
        )


    # Check destination
    destination = df[
        df["Destination"] == location
    ]

    if not destination.empty:

        row = destination.iloc[0]

        return (
            float(row["Dest_Lat"]),
            float(row["Dest_Lon"])
        )


    return None


# ==========================================
# OSRM ROUTING
# ==========================================

def find_route(source, destination):

    source_coordinates = (
        get_location_coordinates(source)
    )

    destination_coordinates = (
        get_location_coordinates(destination)
    )


    if source_coordinates is None:

        return {
            "error":
            f"Coordinates not found for {source}"
        }


    if destination_coordinates is None:

        return {
            "error":
            f"Coordinates not found for {destination}"
        }


    source_lat, source_lon = source_coordinates

    dest_lat, dest_lon = destination_coordinates


    # OSRM expects:
    # longitude,latitude

    url = (
        "https://router.project-osrm.org/"
        "route/v1/driving/"
        f"{source_lon},{source_lat};"
        f"{dest_lon},{dest_lat}"
        "?overview=full"
        "&geometries=geojson"
        "&steps=true"
    )


    try:

        response = requests.get(
            url,
            timeout=15
        )

    except requests.RequestException:

        return {
            "error":
            "Unable to connect to routing service."
        }


    if response.status_code != 200:

        return {
            "error":
            "Unable to connect to routing service."
        }


    data = response.json()


    if data.get("code") != "Ok":

        return {
            "error":
            "No driving route found."
        }


    route = data["routes"][0]


    # --------------------------------------
    # Geometry
    # --------------------------------------

    coordinates = route[
        "geometry"
    ]["coordinates"]


    # Convert:
    # [lon, lat]
    # to:
    # [lat, lon]

    geometry = [
        [coord[1], coord[0]]
        for coord in coordinates
    ]


    # --------------------------------------
    # Distance
    # --------------------------------------

    distance_km = round(
        route["distance"] / 1000,
        2
    )


    # --------------------------------------
    # Duration
    # --------------------------------------

    duration_minutes = round(
        route["duration"] / 60
    )


    return {

        "source": source,

        "destination": destination,

        "distance_km":
            distance_km,

        "estimated_time_minutes":
            duration_minutes,

        "geometry":
            geometry

    }
