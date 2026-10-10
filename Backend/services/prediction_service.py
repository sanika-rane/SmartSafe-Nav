import os
import joblib
import pandas as pd


# ==========================================
# PATHS
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

MODEL_PATH = os.path.join(
    BASE_DIR,
    "..",
    "models",
    "best_model.pkl"
)

SCALER_PATH = os.path.join(
    BASE_DIR,
    "..",
    "models",
    "scaler.pkl"
)

LABEL_PATH = os.path.join(
    BASE_DIR,
    "..",
    "models",
    "label_encoder.pkl"
)


# ==========================================
# LOAD
# ==========================================

model = None

scaler = None

label_encoder = None

df = None


def ensure_loaded():

    global model
    global scaler
    global label_encoder
    global df

    if (
        model is not None
        and scaler is not None
        and label_encoder is not None
        and df is not None
    ):

        return None

    missing_files = [
        path
        for path in [
            MODEL_PATH,
            SCALER_PATH,
            LABEL_PATH,
            DATASET_PATH
        ]
        if not os.path.exists(path)
    ]

    if missing_files:

        return {
            "error": "Required model or data files are missing."
        }

    try:

        model = joblib.load(MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)
        label_encoder = joblib.load(LABEL_PATH)
        df = pd.read_csv(DATASET_PATH)

    except ModuleNotFoundError:

        return {
            "error":
            "Model dependencies are missing. Install backend requirements, including LightGBM."
        }

    except Exception:

        return {
            "error": "Model artifacts could not be loaded."
        }

    return None


# ==========================================
# PREDICT ONE ROAD SEGMENT
# ==========================================

def predict_segment(source, destination, travel_time):

    load_error = ensure_loaded()

    if load_error:

        return load_error

    hour = int(travel_time.split(":")[0])


    # Find both directions
    routes = df[
        (
            (df["Source"] == source) &
            (df["Destination"] == destination)
        )
        |
        (
            (df["Source"] == destination) &
            (df["Destination"] == source)
        )
    ].copy()


    if routes.empty:

        return {
            "error": f"No data found for {source} → {destination}"
        }


    # Find closest time
    routes["hour_difference"] = (
        routes["Hour"] - hour
    ).abs()


    route = routes.sort_values(
        "hour_difference"
    ).iloc[0]


    # --------------------------------------
    # Save original information
    # --------------------------------------

    safety_score = float(
        route["Safety_Score"]
    )

    road_distance = float(
        route["Road_Distance_km"]
    )


    # --------------------------------------
    # Prepare ML input
    # --------------------------------------

    route_data = route.drop(
        labels=["hour_difference"]
    ).to_dict()


    route_df = pd.DataFrame(
        [route_data]
    )


    # Remove target
    route_df = route_df.drop(
        columns=[
            "Safety_Score",
            "Safety_Level"
        ],
        errors="ignore"
    )


    # --------------------------------------
    # One-hot encoding
    # --------------------------------------

    categorical_columns = [

        "Source",
        "Destination",

        "Source_Type",
        "Dest_Type",

        "Road_Type",

        "Season",
        "Weather",

        "Street_Lighting",
        "Visibility",

        "Crowd_Density",

        "Vehicle_Traffic",
        "Pedestrian_Traffic",

        "Crime_Rate",

        "CCTV",
        "Emergency_Booth",

        "Shops_Open",
        "Public_Transport",

        "Road_Condition"
    ]

    existing_categorical_columns = [
        col
        for col in categorical_columns
        if col in route_df.columns
    ]

    for column in existing_categorical_columns:

        route_df[column] = (
            route_df[column]
            .astype(str)
            .str.replace(r"\s+", "_", regex=True)
        )


    route_df = pd.get_dummies(
        route_df,

        columns=existing_categorical_columns,

        dtype=int
    )


    # --------------------------------------
    # Boolean → integer
    # --------------------------------------

    for column in route_df.columns:

        if route_df[column].dtype == bool:

            route_df[column] = (
                route_df[column]
                .astype(int)
            )


    # --------------------------------------
    # Match scaler features
    # --------------------------------------

    scaler_columns = (
        scaler.feature_names_in_
    )


    route_df = route_df.reindex(
        columns=scaler_columns,
        fill_value=0
    )


    # --------------------------------------
    # Scale
    # --------------------------------------

    scaled_features = scaler.transform(
        route_df
    )


    # --------------------------------------
    # ML prediction
    # --------------------------------------

    prediction = model.predict(
        scaled_features
    )


    probabilities = model.predict_proba(
        scaled_features
    )


    # --------------------------------------
    # Label
    # --------------------------------------

    predicted_label = (
        label_encoder
        .inverse_transform(
            prediction.astype(int)
        )[0]
    )


    # --------------------------------------
    # Confidence
    # --------------------------------------

    confidence = round(
        float(max(probabilities[0])) * 100,
        2
    )


    # --------------------------------------
    # Return
    # --------------------------------------

    return {

        "source": source,

        "destination": destination,

        "prediction": predicted_label,

        "confidence": confidence,

        "safety_score": round(
            safety_score,
            2
        ),

        "distance_km": round(
            road_distance,
            2
        ),

        "crime_probability": round(
            float(route["Crime_Probability"]),
            3
        ),

        "lighting":
            route["Street_Lighting"],

        "visibility":
            route["Visibility"],

        "crowd_density":
            route["Crowd_Density"],

        "vehicle_traffic":
            route["Vehicle_Traffic"],

        "cctv":
            route["CCTV"],

        "emergency_booth":
            route["Emergency_Booth"],

        "shops_open":
            route["Shops_Open"],

        "public_transport":
            route["Public_Transport"],

        "weather":
            route["Weather"],

        "police_distance_km":
            round(
                float(
                    route["Police_Distance_km"]
                ),
                2
            )
    }


# ==========================================
# PREDICT COMPLETE ROUTE
# ==========================================

def predict_complete_route(
    path,
    travel_time
):

    segment_results = []


    for i in range(
        len(path) - 1
    ):

        source = path[i]

        destination = path[i + 1]


        result = predict_segment(
            source,
            destination,
            travel_time
        )


        if "error" in result:

            continue


        segment_results.append(
            result
        )


    if not segment_results:

        return {
            "error":
                "Unable to predict route safety."
        }


    # --------------------------------------
    # Overall route safety
    # --------------------------------------

    total_distance = sum(
        segment["distance_km"]
        for segment in segment_results
    )


    weighted_score = sum(
        segment["safety_score"] *
        segment["distance_km"]

        for segment in segment_results
    )


    overall_score = (
        weighted_score /
        total_distance
    )


    # --------------------------------------
    # Overall risk
    # --------------------------------------

    if overall_score >= 70:

        risk_level = "Safe"

    elif overall_score >= 45:

        risk_level = "Moderate"

    else:

        risk_level = "Unsafe"


    # --------------------------------------
    # Confidence
    # --------------------------------------

    confidence = sum(
        segment["confidence"]
        for segment in segment_results
    ) / len(segment_results)


    return {

        "safety_score": round(
            overall_score,
            2
        ),

        "risk_level":
            risk_level,

        "confidence": round(
            confidence,
            2
        ),

        "distance_km": round(
            total_distance,
            2
        ),

        "segments":
            segment_results
    }
