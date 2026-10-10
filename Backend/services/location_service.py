import pandas as pd
import os

# Dataset Path
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DATASET_PATH = os.path.join(
    BASE_DIR,
    "..",
    "data",
    "Synthetic_Dataset.csv"
)


def get_all_locations():

    df = pd.read_csv(DATASET_PATH)

    source = df["Source"].dropna().unique().tolist()

    destination = df["Destination"].dropna().unique().tolist()

    locations = sorted(
        list(
            set(source + destination)
        )
    )

    return locations
