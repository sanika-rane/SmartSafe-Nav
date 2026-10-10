import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DATASET_PATH = os.path.join(
    BASE_DIR,
    "..",
    "data",
    "Synthetic_Dataset.csv"
)


def get_coordinates(location):

    df = pd.read_csv(DATASET_PATH)

    # Search in Source
    source = df[df["Source"] == location]

    if not source.empty:

        row = source.iloc[0]

        return {
            "name": location,
            "lat": float(row["Source_Lat"]),
            "lon": float(row["Source_Lon"])
        }

    # Search in Destination
    destination = df[df["Destination"] == location]

    if not destination.empty:

        row = destination.iloc[0]

        return {
            "name": location,
            "lat": float(row["Dest_Lat"]),
            "lon": float(row["Dest_Lon"])
        }

    return None