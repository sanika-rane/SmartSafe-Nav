# SafePath AI

SafePath AI is a prototype smart-navigation system that ranks driving-route alternatives using predicted safety and multiple contextual factors such as crime probability, street lighting, CCTV, crowd density, weather, public transport, emergency booths, and police distance.

> This is a research/demo prototype. A `Safe` result is a model prediction, not a guarantee of personal safety. The current system uses synthetic data and ranks alternatives returned by OSRM; it does not yet search a fully safety-weighted road graph.

## Project Structure

```text
Backend/       Flask API, routes, safety scoring, and model inference
data/          Synthetic dataset and train/test CSV files
models/        Serialized model, scaler, and label encoder
notebooks/     EDA, preprocessing, training, evaluation, SHAP, and routing work
frontend/      React + Vite + Leaflet client
PROJECT_REVIEW.md
```

The top-level folders are the canonical project. The nested `ML_CP/` directory is a duplicate copy and should not be used for new development.

## Requirements

- Windows, macOS, or Linux
- Python 3.11 recommended
- Node.js 18 or newer and npm
- Internet access for OSRM routing and OpenStreetMap map tiles

The backend dependencies are listed in [Backend/requirements.txt](Backend/requirements.txt). The saved model requires `lightgbm` to be installed before it can be loaded.

## Backend Setup

Open PowerShell in the project root:

```powershell
cd Backend
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python app.py
```

The API starts at `http://127.0.0.1:5000`.

Verify the health response in another terminal:

```powershell
Invoke-RestMethod http://127.0.0.1:5000/
```

If PowerShell blocks activation, run the commands from an activated terminal or use:

```powershell
.\.venv\Scripts\python.exe app.py
```

## Frontend Setup

Open a second terminal in the project root:

```powershell
cd frontend
npm install
Copy-Item .env.example .env.local
npm run dev
```

Open the Vite URL shown in the terminal, normally `http://localhost:5173`.

The frontend reads the backend URL from `VITE_API_BASE_URL`. The default is `http://127.0.0.1:5000`, so `.env.local` is optional for local development. For another backend URL, set:

```text
VITE_API_BASE_URL=http://127.0.0.1:5000
```

Useful frontend commands:

```powershell
npm run dev       # Start the development server
npm run build     # Create a production build
npm run preview   # Preview the production build
npm run lint      # Run Oxlint
```

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Backend status response. |
| `/locations` | GET | Returns available source and destination names. |
| `/coordinates?location=...` | GET | Returns coordinates for a known location. |
| `/find-route` | POST | Returns one OSRM route. |
| `/predict-route` | POST | Predicts safety for a named route path. |
| `/safe-routes` | POST | Returns OSRM alternatives ranked by safety score. |
| `/model-readiness` | GET | Reports whether data/model/scaler/label artifacts can be loaded. |

Example request:

```powershell
$body = @{ source = "Location A"; destination = "Location B"; time = "18:00" } | ConvertTo-Json
Invoke-RestMethod -Uri http://127.0.0.1:5000/safe-routes -Method Post -ContentType 'application/json' -Body $body
```

Use location names returned by `/locations`; the example names above are placeholders.

`/safe-routes` validates JSON input before scoring. It requires `source`, `destination`, and `time` in `HH:mm` format, rejects identical endpoints, returns stable error codes, and avoids exposing raw internal exception strings.

Example response shape:

```json
{
  "source": "Kothrud",
  "destination": "Baner",
  "time": "18:00",
  "routes": [
    {
      "route_type": "Safest",
      "safety_score": 78.4,
      "risk_level": "Safe",
      "confidence": 84.1,
      "predicted_probability": 84.1,
      "model_confidence_note": "This value is the average maximum class probability with a route-variation penalty; it is not a guarantee.",
      "score_weights": {
        "ml_score": 0.7,
        "factor_score": 0.3
      },
      "explanation": {
        "summary": "This route ranked highest because its sampled points had stronger predicted safety factors.",
        "status": "available",
        "method": "shap_tree_explainer",
        "positive_factors": [
          {
            "feature": "Street lighting",
            "impact": "positive",
            "reason": "Street lighting was associated with a higher predicted safety score for this route.",
            "contribution": 4.8
          }
        ],
        "negative_factors": [],
        "rule_based_explanations": [
          "CCTV is available nearby."
        ],
        "comparison": "Ranked above the alternatives because its final hybrid safety score was highest."
      }
    }
  ],
  "metadata": {
    "data_source": "Synthetic_Dataset.csv",
    "model_version": "best_model.pkl",
    "explanation_method": "shap_tree_explainer"
  }
}
```

The route score currently remains:

```text
final_score = 0.70 * ml_score + 0.30 * factor_score
```

`confidence` is preserved for compatibility. New code should prefer `predicted_probability` and read `model_confidence_note`.

## Model and Data Files

The backend loads these files from the project root:

- `data/Synthetic_Dataset.csv`
- `models/best_model.pkl`
- `models/scaler.pkl`
- `models/label_encoder.pkl`

The model pipeline uses one-hot encoded categorical features and aligns inference columns with the saved scaler. The route score combines the ML prediction with a rule-based factor score. See [PROJECT_REVIEW.md](PROJECT_REVIEW.md) for the full architecture review, known limitations, and roadmap.

## Explainability

The `/safe-routes` response includes a readable explanation for each candidate route. When SHAP works with the saved LightGBM model, the backend aggregates local model contributions across sampled route points and returns top positive and negative factors. These factors describe what contributed to the model prediction; they do not prove causality or guarantee real-world safety.

If SHAP is unavailable or fails for a request, the API still returns route results with `explanation.status` set to `fallback` and includes rule-based safety checks such as CCTV availability, lighting, police distance, public transport, shops open, and late-night travel.

## Troubleshooting

- **`ModuleNotFoundError: lightgbm`**: activate the backend virtual environment and run `python -m pip install -r requirements.txt`.
- **Broken checked-in virtual environment**: recreate it with `python -m venv .venv`; do not rely on a venv copied from another machine or Python version.
- **Frontend cannot connect**: confirm the Flask server is running on port 5000 and check `VITE_API_BASE_URL`.
- **`npm run dev` exits while loading Vite config**: this project now uses a minimal `vite.config.js` to avoid the plugin externalization path that can fail with `spawn EPERM` on some Windows setups. Run `npm install` and then `npm run dev` again.
- **No route returned**: confirm both locations exist in `/locations` and that OSRM is reachable.
- **Map is blank**: check internet access because Leaflet loads OpenStreetMap tiles remotely.
- **PowerShell execution policy error**: use the venv interpreter directly with `\.venv\Scripts\python.exe`, or activate the environment using your team's approved shell policy.

## Validation

From `frontend/`, run `npm run build`. For backend validation, run:

```powershell
cd Backend
python -m compileall app.py routes services test_model.py test_safe_routes.py
python -m unittest test_safe_routes.py
python test_model.py
```

The backend smoke test requires all dependencies from `requirements.txt` and compatible serialized model artifacts.
