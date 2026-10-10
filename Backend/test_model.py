import joblib
import os


# --------------------------------------------------
# Project root
# --------------------------------------------------

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


# --------------------------------------------------
# Model paths
# --------------------------------------------------

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


# --------------------------------------------------
# Check paths
# --------------------------------------------------

print("\n========== FILE PATHS ==========")

print("Model:", MODEL_PATH)
print("Scaler:", SCALER_PATH)
print("Label Encoder:", LABEL_PATH)

print("\nModel exists:", os.path.exists(MODEL_PATH))
print("Scaler exists:", os.path.exists(SCALER_PATH))
print("Label Encoder exists:", os.path.exists(LABEL_PATH))


# --------------------------------------------------
# Load files
# --------------------------------------------------

model = joblib.load(MODEL_PATH)

scaler = joblib.load(SCALER_PATH)

label_encoder = joblib.load(LABEL_PATH)


# --------------------------------------------------
# Display model information
# --------------------------------------------------

print("\n========== MODEL INFORMATION ==========")

print("\nModel type:")
print(type(model))

print("\nNumber of features:")
print(model.n_features_)

print("\nFeature names:")
print(model.feature_name_)

print("\nScaler type:")
print(type(scaler))

print("\nLabel Encoder type:")
print(type(label_encoder))

print("\nClasses:")
print(label_encoder.classes_)

print("\n======================================")