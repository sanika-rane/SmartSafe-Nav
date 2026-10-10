import os
import joblib
import pandas as pd


BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "best_model.pkl"
)

SCALER_PATH = os.path.join(
    BASE_DIR,
    "models",
    "scaler.pkl"
)

LABEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "label_encoder.pkl"
)


model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)
label_encoder = joblib.load(LABEL_PATH)


def predict_route(features):

    df = pd.DataFrame([features])

    df_scaled = scaler.transform(df)

    prediction = model.predict(df_scaled)

    probabilities = model.predict_proba(df_scaled)

    predicted_label = label_encoder.inverse_transform(
        prediction
    )[0]

    confidence = round(
        max(probabilities[0]) * 100,
        2
    )

    return {
        "prediction": predicted_label,
        "confidence": confidence
    }