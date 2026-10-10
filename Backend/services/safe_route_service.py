import logging
import os
from datetime import datetime, timezone

import joblib
import pandas as pd
import requests


logger = logging.getLogger(__name__)


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

PROJECT_ROOT = os.path.abspath(
    os.path.join(
        BASE_DIR,
        ".."
    )
)

DATASET_PATH = os.path.join(
    PROJECT_ROOT,
    "data",
    "Synthetic_Dataset.csv"
)

MODEL_PATH = os.path.join(
    PROJECT_ROOT,
    "models",
    "best_model.pkl"
)

SCALER_PATH = os.path.join(
    PROJECT_ROOT,
    "models",
    "scaler.pkl"
)

LABEL_PATH = os.path.join(
    PROJECT_ROOT,
    "models",
    "label_encoder.pkl"
)

REQUIRED_FILES = {
    "dataset": DATASET_PATH,
    "model": MODEL_PATH,
    "scaler": SCALER_PATH,
    "label_encoder": LABEL_PATH,
}

REQUIRED_COLUMNS = [
    "Source",
    "Destination",
    "Source_Lat",
    "Source_Lon",
    "Dest_Lat",
    "Dest_Lon",
    "Safety_Score",
    "Safety_Level",
    "Hour",
    "Crime_Probability",
    "Theft_Reports",
    "Harassment_Reports",
    "Police_Distance_km",
    "Street_Lighting",
    "Visibility",
    "Crowd_Density",
    "Vehicle_Traffic",
    "Weather",
    "CCTV",
    "Emergency_Booth",
    "Shops_Open",
    "Public_Transport",
    "Road_Condition",
]

CATEGORICAL_COLUMNS = [
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
    "Road_Condition",
]

FEATURE_LABELS = {
    "Crime_Probability": "Crime probability",
    "Street_Lighting": "Street lighting",
    "Police_Distance_km": "Police distance",
    "CCTV": "CCTV availability",
    "Emergency_Booth": "Emergency booth availability",
    "Crowd_Density": "Crowd density",
    "Visibility": "Visibility",
    "Weather": "Weather",
    "Road_Condition": "Road condition",
    "Public_Transport": "Public transport",
    "Shops_Open": "Shops open",
    "Theft_Reports": "Theft reports",
    "Harassment_Reports": "Harassment reports",
}

ONE_HOT_PREFIXES = [
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
    "Road_Condition",
]

ML_WEIGHT = 0.70
FACTOR_WEIGHT = 0.30

_dataset = None
_model = None
_scaler = None
_label_encoder = None
_shap_explainer = None
_shap_error = None
_load_error = None
_prediction_cache = {}


class ServiceError(Exception):
    def __init__(self, message, status_code=400, code="bad_request"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


def error_response(message, status_code=400, code="bad_request"):
    return {
        "error": message,
        "code": code,
        "status_code": status_code,
    }


def ensure_runtime_ready():
    global _dataset
    global _model
    global _scaler
    global _label_encoder
    global _load_error

    if _load_error:
        raise ServiceError(
            _load_error,
            503,
            "model_unavailable"
        )

    if (
        _dataset is not None
        and _model is not None
        and _scaler is not None
        and _label_encoder is not None
    ):
        return

    missing_files = [
        name
        for name, path in REQUIRED_FILES.items()
        if not os.path.exists(path)
    ]

    if missing_files:
        raise ServiceError(
            "Required runtime files are missing: "
            + ", ".join(missing_files),
            503,
            "missing_runtime_files"
        )

    try:
        dataset = pd.read_csv(DATASET_PATH)
    except Exception:
        logger.exception("Unable to read safety dataset")
        raise ServiceError(
            "Safety dataset could not be loaded.",
            503,
            "dataset_unavailable"
        )

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in dataset.columns
    ]

    if missing_columns:
        raise ServiceError(
            "Safety dataset is missing required columns: "
            + ", ".join(missing_columns),
            503,
            "dataset_schema_error"
        )

    try:
        _model = joblib.load(MODEL_PATH)
        _scaler = joblib.load(SCALER_PATH)
        _label_encoder = joblib.load(LABEL_PATH)
        _dataset = dataset.fillna(
            {
                "Crime_Probability": 0,
                "Theft_Reports": 0,
                "Harassment_Reports": 0,
                "Police_Distance_km": 10,
            }
        )
    except ModuleNotFoundError as error:
        _load_error = (
            "Model dependencies are missing. Install backend "
            "requirements, including LightGBM."
        )
        logger.warning("Model dependency missing: %s", error.name)
        raise ServiceError(
            _load_error,
            503,
            "model_dependency_missing"
        )
    except Exception:
        logger.exception("Unable to load model artifacts")
        raise ServiceError(
            "Model artifacts could not be loaded.",
            503,
            "model_unavailable"
        )


def get_dataset():
    ensure_runtime_ready()
    return _dataset


def readiness_status():
    try:
        ensure_runtime_ready()
    except ServiceError as error:
        return {
            "ready": False,
            "error": error.message,
            "code": error.code,
            "files": {
                name: os.path.exists(path)
                for name, path in REQUIRED_FILES.items()
            },
        }

    return {
        "ready": True,
        "model_type": type(_model).__name__,
        "feature_count": len(_scaler.feature_names_in_),
        "classes": list(_label_encoder.classes_),
        "files": {
            name: True
            for name in REQUIRED_FILES
        },
    }


def get_location_coordinates(location):
    df = get_dataset()

    source = df[df["Source"] == location]

    if not source.empty:
        row = source.iloc[0]
        return (
            float(row["Source_Lat"]),
            float(row["Source_Lon"])
        )

    destination = df[df["Destination"] == location]

    if not destination.empty:
        row = destination.iloc[0]
        return (
            float(row["Dest_Lat"]),
            float(row["Dest_Lon"])
        )

    return None


def find_nearest_records(lat, lon, number_of_records=5):
    df = get_dataset()

    source_distance = (
        (df["Source_Lat"] - lat) ** 2
        + (df["Source_Lon"] - lon) ** 2
    )

    destination_distance = (
        (df["Dest_Lat"] - lat) ** 2
        + (df["Dest_Lon"] - lon) ** 2
    )

    distance = pd.concat(
        [
            source_distance,
            destination_distance,
        ],
        axis=1
    ).min(axis=1)

    nearest_indexes = (
        distance
        .nsmallest(number_of_records)
        .index
    )

    records = []

    for index in nearest_indexes:
        record = df.loc[index].copy()
        record["_distance"] = float(distance.loc[index])
        record["_record_index"] = int(index)
        records.append(record)

    return records


def prepare_features(row):
    ensure_runtime_ready()

    route_df = pd.DataFrame([row.to_dict()])

    route_df = route_df.drop(
        columns=[
            "Safety_Score",
            "Safety_Level",
            "_distance",
        ],
        errors="ignore"
    )

    existing_columns = [
        column
        for column in CATEGORICAL_COLUMNS
        if column in route_df.columns
    ]

    for column in existing_columns:
        route_df[column] = (
            route_df[column]
            .astype(str)
            .str.replace(r"\s+", "_", regex=True)
        )

    route_df = pd.get_dummies(
        route_df,
        columns=existing_columns,
        dtype=int
    )

    for column in route_df.columns:
        if route_df[column].dtype == bool:
            route_df[column] = route_df[column].astype(int)

    route_df = route_df.reindex(
        columns=_scaler.feature_names_in_,
        fill_value=0
    )

    route_df = route_df.fillna(0)

    return route_df


def prepare_scaled_features(row):
    features = prepare_features(row)
    scaled_features = _scaler.transform(features)

    return features, scaled_features


def get_ml_prediction(row, hour):
    row = row.copy()
    row["Hour"] = hour

    features, scaled_features = prepare_scaled_features(row)

    try:
        prediction = _model.predict(scaled_features)
        probabilities = _model.predict_proba(scaled_features)[0]
    except Exception:
        logger.exception("Model prediction failed")
        raise ServiceError(
            "Safety prediction could not be calculated.",
            500,
            "prediction_failed"
        )

    predicted_label = (
        _label_encoder
        .inverse_transform(prediction.astype(int))[0]
    )

    class_names = list(_label_encoder.classes_)

    safe_probability = 0
    if "Safe" in class_names:
        safe_index = class_names.index("Safe")
        safe_probability = probabilities[safe_index] * 100

    predicted_index = class_names.index(predicted_label)
    confidence = max(probabilities) * 100

    return {
        "ml_score": float(safe_probability),
        "predicted_probability": float(confidence),
        "prediction": predicted_label,
        "predicted_class_index": predicted_index,
        "features": features,
        "scaled_features": scaled_features,
    }


def calculate_factor_score(row, hour):
    df = get_dataset()
    score = 100.0

    crime_probability = float(row.get("Crime_Probability", 0))
    score -= crime_probability * 25

    theft = float(row.get("Theft_Reports", 0))
    theft_max = max(float(df["Theft_Reports"].max()), 1)
    score -= (theft / theft_max) * 8

    harassment = float(row.get("Harassment_Reports", 0))
    harassment_max = max(float(df["Harassment_Reports"].max()), 1)
    score -= (harassment / harassment_max) * 10

    lighting = str(row.get("Street_Lighting", "Unknown"))
    if lighting == "High":
        score += 8
    elif lighting == "Medium":
        score += 2
    elif lighting == "Low":
        score -= 10

    if str(row.get("CCTV", "No")) == "Yes":
        score += 6
    else:
        score -= 5

    if str(row.get("Emergency_Booth", "No")) == "Yes":
        score += 5
    else:
        score -= 3

    police_distance = float(row.get("Police_Distance_km", 10))
    if police_distance <= 1:
        score += 6
    elif police_distance <= 2:
        score += 3
    elif police_distance <= 4:
        score -= 2
    else:
        score -= 6

    crowd = str(row.get("Crowd_Density", "Unknown"))
    if crowd == "High":
        score += 5
    elif crowd == "Medium":
        score += 2
    elif crowd == "Low":
        score -= 5

    if str(row.get("Shops_Open", "No")) == "Yes":
        score += 4
    else:
        score -= 3

    if str(row.get("Public_Transport", "No")) == "Yes":
        score += 3
    else:
        score -= 2

    visibility = str(row.get("Visibility", "Unknown"))
    if visibility == "High":
        score += 4
    elif visibility == "Medium":
        score += 1
    elif visibility == "Low":
        score -= 5

    weather = str(row.get("Weather", "Unknown"))
    if weather == "Clear":
        score += 3
    elif weather == "Rain":
        score -= 3
    elif weather == "Fog":
        score -= 5

    road_condition = str(row.get("Road_Condition", "Unknown"))
    if road_condition == "Good":
        score += 4
    elif road_condition == "Poor":
        score -= 5

    if hour >= 22 or hour <= 5:
        score -= 5

    return max(0, min(100, score))


def rule_based_explanations(row, hour):
    explanations = []

    if str(row.get("CCTV", "No")) == "Yes":
        explanations.append("CCTV is available nearby.")

    if str(row.get("Emergency_Booth", "No")) == "Yes":
        explanations.append("An emergency booth is available nearby.")

    police_distance = float(row.get("Police_Distance_km", 10))
    if police_distance <= 2:
        explanations.append("Police support is within 2 km.")
    elif police_distance > 4:
        explanations.append("Police support is more than 4 km away.")

    lighting = str(row.get("Street_Lighting", "Unknown"))
    if lighting == "High":
        explanations.append("Street lighting is high.")
    elif lighting == "Low":
        explanations.append("Street lighting is low.")

    crime_probability = float(row.get("Crime_Probability", 0))
    if crime_probability >= 0.65:
        explanations.append("Crime probability is elevated in nearby records.")
    elif crime_probability <= 0.30:
        explanations.append("Crime probability is lower in nearby records.")

    crowd = str(row.get("Crowd_Density", "Unknown"))
    if crowd == "High":
        explanations.append("Crowd density is high.")
    elif crowd == "Low":
        explanations.append("Crowd density is low.")

    if str(row.get("Shops_Open", "No")) == "Yes":
        explanations.append("Shops are open along nearby records.")

    if str(row.get("Public_Transport", "No")) == "Yes":
        explanations.append("Public transport is available nearby.")

    if hour >= 22 or hour <= 5:
        explanations.append("Late-night travel reduced the rule-based score.")

    return explanations[:6]


def feature_group(feature_name):
    for prefix in sorted(
        ONE_HOT_PREFIXES,
        key=len,
        reverse=True
    ):
        if feature_name == prefix or feature_name.startswith(prefix + "_"):
            return prefix

    return feature_name


def readable_feature_name(feature_name):
    group = feature_group(feature_name)
    return FEATURE_LABELS.get(
        group,
        group.replace("_", " ")
    )


def get_shap_explainer():
    global _shap_explainer
    global _shap_error

    if _shap_error:
        return None

    if _shap_explainer is not None:
        return _shap_explainer

    try:
        import shap

        _shap_explainer = shap.TreeExplainer(_model)
        return _shap_explainer
    except Exception as error:
        _shap_error = str(error)
        logger.info("SHAP unavailable: %s", type(error).__name__)
        return None


def extract_shap_values(shap_values, class_index):
    if isinstance(shap_values, list):
        return shap_values[class_index][0]

    shape = getattr(shap_values, "shape", None)

    if shape is not None and len(shape) == 3:
        return shap_values[0, :, class_index]

    if shape is not None and len(shape) == 2:
        return shap_values[0]

    return shap_values


def model_contributions(prediction):
    explainer = get_shap_explainer()

    if explainer is None:
        return {
            "status": "fallback",
            "method": "rule_based_only",
            "contributions": [],
            "message": (
                "Model contribution details were unavailable, so "
                "rule-based safety checks were returned."
            ),
        }

    try:
        values = explainer.shap_values(prediction["scaled_features"])
        class_values = extract_shap_values(
            values,
            prediction["predicted_class_index"]
        )
    except Exception:
        logger.exception("SHAP explanation failed")
        return {
            "status": "fallback",
            "method": "rule_based_only",
            "contributions": [],
            "message": (
                "Model explanation could not be calculated for this "
                "route, so rule-based safety checks were returned."
            ),
        }

    grouped = {}

    for feature_name, value in zip(
        prediction["features"].columns,
        class_values
    ):
        group = feature_group(feature_name)
        grouped[group] = grouped.get(group, 0.0) + float(value)

    contributions = [
        {
            "feature": readable_feature_name(feature),
            "raw_feature_group": feature,
            "contribution": round(value, 2),
            "impact": "positive" if value >= 0 else "negative",
            "reason": (
                f"{readable_feature_name(feature)} contributed to "
                "a higher predicted safety score."
                if value >= 0
                else f"{readable_feature_name(feature)} contributed to "
                "a lower predicted safety score."
            ),
        }
        for feature, value in grouped.items()
        if abs(value) > 0.001
    ]

    contributions.sort(
        key=lambda item: abs(item["contribution"]),
        reverse=True
    )

    return {
        "status": "available",
        "method": "shap_tree_explainer",
        "contributions": contributions,
        "message": (
            "Model factors show associations in the prediction, "
            "not causes of real-world safety."
        ),
    }


def predict_record(row, hour, explain=True):
    cache_key = None

    if "_record_index" in row:
        cache_key = (
            int(row["_record_index"]),
            int(hour),
            bool(explain),
        )

    if cache_key in _prediction_cache:
        return _prediction_cache[cache_key].copy()

    ml_prediction = get_ml_prediction(row, hour)
    factor_score = calculate_factor_score(row, hour)

    final_score = (
        ML_WEIGHT * ml_prediction["ml_score"]
        + FACTOR_WEIGHT * factor_score
    )

    final_score = max(0, min(100, final_score))

    if explain:
        shap_details = model_contributions(ml_prediction)
        rule_factors = rule_based_explanations(row, hour)
    else:
        shap_details = {
            "status": "skipped",
            "method": "not_requested",
            "contributions": [],
            "message": "Explanation was calculated for the nearest sampled record only.",
        }
        rule_factors = []

    result = {
        "prediction": ml_prediction["prediction"],
        "ml_score": round(ml_prediction["ml_score"], 2),
        "factor_score": round(factor_score, 2),
        "safety_score": round(final_score, 2),
        "confidence": round(ml_prediction["predicted_probability"], 2),
        "predicted_probability": round(
            ml_prediction["predicted_probability"],
            2
        ),
        "crime_probability": round(
            float(row.get("Crime_Probability", 0)),
            3
        ),
        "lighting": str(row.get("Street_Lighting", "Unknown")),
        "visibility": str(row.get("Visibility", "Unknown")),
        "crowd_density": str(row.get("Crowd_Density", "Unknown")),
        "vehicle_traffic": str(row.get("Vehicle_Traffic", "Unknown")),
        "weather": str(row.get("Weather", "Unknown")),
        "cctv": str(row.get("CCTV", "Unknown")),
        "emergency_booth": str(row.get("Emergency_Booth", "Unknown")),
        "police_distance_km": round(
            float(row.get("Police_Distance_km", 0)),
            2
        ),
        "ml_contributions": shap_details["contributions"],
        "explanation_status": shap_details["status"],
        "explanation_method": shap_details["method"],
        "explanation_message": shap_details["message"],
        "rule_based_factors": rule_factors,
    }

    if cache_key is not None:
        _prediction_cache[cache_key] = result.copy()

    return result


def predict_route_point(lat, lon, hour):
    records = find_nearest_records(
        lat,
        lon,
        number_of_records=5
    )

    predictions = []
    weights = []

    for index, row in enumerate(records):
        distance = row["_distance"]
        weight = 1 / (distance + 0.000001)
        prediction = predict_record(
            row,
            hour,
            explain=index == 0
        )
        predictions.append(prediction)
        weights.append(weight)

    total_weight = sum(weights)

    weighted_score = (
        sum(
            prediction["safety_score"] * weight
            for prediction, weight in zip(predictions, weights)
        )
        / total_weight
    )

    weighted_confidence = (
        sum(
            prediction["confidence"] * weight
            for prediction, weight in zip(predictions, weights)
        )
        / total_weight
    )

    closest = predictions[0]

    return {
        "safety_score": round(weighted_score, 2),
        "confidence": round(weighted_confidence, 2),
        "predicted_probability": round(weighted_confidence, 2),
        "prediction": closest["prediction"],
        "crime_probability": closest["crime_probability"],
        "lighting": closest["lighting"],
        "visibility": closest["visibility"],
        "crowd_density": closest["crowd_density"],
        "vehicle_traffic": closest["vehicle_traffic"],
        "weather": closest["weather"],
        "cctv": closest["cctv"],
        "emergency_booth": closest["emergency_booth"],
        "police_distance_km": closest["police_distance_km"],
        "ml_contributions": closest["ml_contributions"],
        "explanation_status": closest["explanation_status"],
        "explanation_method": closest["explanation_method"],
        "explanation_message": closest["explanation_message"],
        "rule_based_factors": closest["rule_based_factors"],
    }


def get_osrm_routes(source, destination):
    source_coordinates = get_location_coordinates(source)
    destination_coordinates = get_location_coordinates(destination)

    if source_coordinates is None:
        raise ServiceError(
            f"Unknown location: {source}",
            404,
            "unknown_location"
        )

    if destination_coordinates is None:
        raise ServiceError(
            f"Unknown location: {destination}",
            404,
            "unknown_location"
        )

    source_lat, source_lon = source_coordinates
    destination_lat, destination_lon = destination_coordinates

    url = (
        "https://router.project-osrm.org/"
        "route/v1/driving/"
        f"{source_lon},{source_lat};"
        f"{destination_lon},{destination_lat}"
        "?alternatives=3"
        "&overview=full"
        "&geometries=geojson"
    )

    try:
        response = requests.get(url, timeout=15)
    except requests.RequestException:
        logger.warning("OSRM request failed")
        raise ServiceError(
            "Routing service is unavailable. Please try again later.",
            503,
            "osrm_unavailable"
        )

    if response.status_code != 200:
        logger.warning("OSRM returned HTTP %s", response.status_code)
        raise ServiceError(
            "Routing service is unavailable. Please try again later.",
            503,
            "osrm_unavailable"
        )

    data = response.json()

    if data.get("code") != "Ok" or not data.get("routes"):
        raise ServiceError(
            "No route found for the selected locations.",
            404,
            "no_route_found"
        )

    return data["routes"]


def get_sample_points(coordinates):
    n = len(coordinates)

    if n <= 7:
        return coordinates

    indexes = [
        0,
        n // 6,
        (2 * n) // 6,
        (3 * n) // 6,
        (4 * n) // 6,
        (5 * n) // 6,
        n - 1,
    ]

    return [
        coordinates[index]
        for index in indexes
    ]


def median(values):
    sorted_values = sorted(values)
    middle = len(sorted_values) // 2

    if len(sorted_values) % 2 == 0:
        return (
            sorted_values[middle - 1]
            + sorted_values[middle]
        ) / 2

    return sorted_values[middle]


def aggregate_factor_lists(point_predictions, key):
    seen = []

    for prediction in point_predictions:
        for factor in prediction.get(key, []):
            if factor not in seen:
                seen.append(factor)

    return seen[:6]


def aggregate_ml_contributions(point_predictions):
    totals = {}

    status = "available"
    method = "shap_tree_explainer"
    message = (
        "Model factors show associations in the prediction, not "
        "causes of real-world safety."
    )

    for prediction in point_predictions:
        if prediction.get("explanation_status") != "available":
            status = prediction.get("explanation_status", "fallback")
            method = prediction.get("explanation_method", "rule_based_only")
            message = prediction.get(
                "explanation_message",
                "Model explanation details were unavailable."
            )

        for contribution in prediction.get("ml_contributions", []):
            feature = contribution["feature"]
            totals[feature] = totals.get(feature, 0.0) + float(
                contribution["contribution"]
            )

    count = max(len(point_predictions), 1)

    contributions = [
        {
            "feature": feature,
            "contribution": round(value / count, 2),
            "impact": "positive" if value >= 0 else "negative",
            "reason": (
                f"{feature} was associated with a higher predicted "
                "safety score for this route."
                if value >= 0
                else f"{feature} was associated with a lower predicted "
                "safety score for this route."
            ),
        }
        for feature, value in totals.items()
        if abs(value / count) > 0.001
    ]

    positive = sorted(
        [
            item
            for item in contributions
            if item["contribution"] >= 0
        ],
        key=lambda item: item["contribution"],
        reverse=True
    )[:5]

    negative = sorted(
        [
            item
            for item in contributions
            if item["contribution"] < 0
        ],
        key=lambda item: item["contribution"]
    )[:5]

    return {
        "status": status,
        "method": method,
        "message": message,
        "positive_factors": positive,
        "negative_factors": negative,
    }


def build_route_explanation(route, point_predictions):
    ml_summary = aggregate_ml_contributions(point_predictions)
    rule_factors = aggregate_factor_lists(
        point_predictions,
        "rule_based_factors"
    )

    positive_features = [
        item["feature"]
        for item in ml_summary["positive_factors"][:3]
    ]

    if positive_features:
        summary = (
            "This route ranked highest because its sampled points "
            "had stronger predicted safety factors such as "
            + ", ".join(positive_features)
            + "."
        )
    else:
        summary = (
            "This route ranked highest by the hybrid safety score, "
            "using model probability and rule-based safety checks."
        )

    comparison = route.get(
        "route_comparison_reason",
        "Ranked by final safety score against the alternatives."
    )

    return {
        "summary": summary,
        "status": ml_summary["status"],
        "explanation_status": ml_summary["status"],
        "method": ml_summary["method"],
        "explanation_method": ml_summary["method"],
        "message": ml_summary["message"],
        "ml_explanations": {
            "status": ml_summary["status"],
            "method": ml_summary["method"],
            "positive_factors": ml_summary["positive_factors"],
            "negative_factors": ml_summary["negative_factors"],
        },
        "positive_factors": ml_summary["positive_factors"],
        "negative_factors": ml_summary["negative_factors"],
        "risk_factors": ml_summary["negative_factors"],
        "rule_based_explanations": rule_factors,
        "rule_based_factors": rule_factors,
        "comparison": comparison,
        "route_comparison_reason": comparison,
    }


def score_route(route, travel_time):
    hour = int(travel_time.split(":")[0])
    coordinates = route["geometry"]["coordinates"]
    selected_coordinates = get_sample_points(coordinates)

    point_predictions = []

    for coordinate in selected_coordinates:
        lon = coordinate[0]
        lat = coordinate[1]
        prediction = predict_route_point(lat, lon, hour)
        point_predictions.append(prediction)

    if not point_predictions:
        raise ServiceError(
            "No route found for the selected locations.",
            404,
            "no_route_found"
        )

    scores = [
        item["safety_score"]
        for item in point_predictions
    ]

    average_score = sum(scores) / len(scores)
    median_score = median(scores)

    final_score = (
        0.6 * average_score
        + 0.4 * median_score
    )

    final_score = max(0, min(100, final_score))

    if final_score >= 70:
        risk_level = "Safe"
    elif final_score >= 45:
        risk_level = "Moderate"
    else:
        risk_level = "Unsafe"

    confidences = [
        item["confidence"]
        for item in point_predictions
    ]

    average_confidence = sum(confidences) / len(confidences)
    variation = max(scores) - min(scores)
    penalty = min(15, variation * 0.15)
    final_confidence = average_confidence - penalty
    final_confidence = max(50, min(99, final_confidence))

    geometry = [
        [
            coordinate[1],
            coordinate[0],
        ]
        for coordinate in coordinates
    ]

    scored_route = {
        "safety_score": round(final_score, 2),
        "risk_level": risk_level,
        "confidence": round(final_confidence, 2),
        "predicted_probability": round(final_confidence, 2),
        "model_confidence_note": (
            "This value is the average maximum class probability "
            "with a route-variation penalty; it is not a guarantee."
        ),
        "distance_km": round(route["distance"] / 1000, 2),
        "estimated_time_minutes": round(route["duration"] / 60),
        "geometry": geometry,
        "safety_details": point_predictions,
        "score_weights": {
            "ml_score": ML_WEIGHT,
            "factor_score": FACTOR_WEIGHT,
        },
    }

    scored_route["explanation"] = build_route_explanation(
        scored_route,
        point_predictions
    )

    return scored_route


def find_safest_routes(source, destination, travel_time):
    try:
        ensure_runtime_ready()
        routes = get_osrm_routes(source, destination)

        results = []

        for route in routes:
            scored = score_route(route, travel_time)
            results.append(scored)

        if not results:
            raise ServiceError(
                "No route found for the selected locations.",
                404,
                "no_route_found"
            )

        results.sort(
            key=lambda item: item["safety_score"],
            reverse=True
        )

        best_score = results[0]["safety_score"]

        for index, route in enumerate(results):
            if index == 0:
                route["route_type"] = "Safest"
                route["route_comparison_reason"] = (
                    "Ranked above the alternatives because its final "
                    "hybrid safety score was highest."
                )
            elif index == 1:
                route["route_type"] = "Alternative"
                route["route_comparison_reason"] = (
                    f"Scored {round(best_score - route['safety_score'], 2)} "
                    "points below the safest route."
                )
            else:
                route["route_type"] = "Higher Risk"
                route["route_comparison_reason"] = (
                    f"Scored {round(best_score - route['safety_score'], 2)} "
                    "points below the safest route."
                )

            route["explanation"] = build_route_explanation(
                route,
                route.get("safety_details", [])
            )

        explanation_methods = {
            route["explanation"]["method"]
            for route in results
        }

        return {
            "source": source,
            "destination": destination,
            "time": travel_time,
            "routes": results,
            "metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "data_source": "Synthetic_Dataset.csv",
                "model_version": os.path.basename(MODEL_PATH),
                "score_weights": {
                    "ml_score": ML_WEIGHT,
                    "factor_score": FACTOR_WEIGHT,
                },
                "explanation_method": (
                    "shap_tree_explainer"
                    if "shap_tree_explainer" in explanation_methods
                    else "rule_based_only"
                ),
                "limitations": (
                    "Routes are OSRM alternatives ranked with synthetic "
                    "data; predicted safety is not guaranteed safety."
                ),
            },
        }
    except ServiceError as error:
        return error_response(
            error.message,
            error.status_code,
            error.code
        )
    except Exception:
        logger.exception("Unexpected safe route failure")
        return error_response(
            "Unable to calculate safe routes right now.",
            500,
            "internal_error"
        )
