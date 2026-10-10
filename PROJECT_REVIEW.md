# SmartSafe Nav Project Review

## 1. Executive Summary

SafePath AI is a prototype smart-navigation application that combines:

- A synthetic safety dataset containing route, environment, crime, infrastructure, and traffic factors.
- A saved machine-learning classifier that predicts a safety label.
- A rule-based safety-factor score that adds domain-specific adjustments.
- OSRM, an external routing service, to generate up to three driving-route alternatives.
- A Flask backend that scores the alternatives.
- A React/Vite frontend that presents route scores, risk levels, safety factors, and Leaflet maps.

The current product demonstrates the intended end-to-end workflow, but it should be described as a research/demo prototype rather than a production safety service. The most important limitation is that the system does not calculate a route from a safety-weighted road graph. It first receives alternatives from OSRM and then ranks those alternatives using sampled safety predictions. If OSRM does not return a route that is safer, the application cannot discover one.

### Overall assessment

| Area | Assessment | Main observation |
|---|---|---|
| Product concept | Promising prototype | Clear focus on safety-aware travel assistance. |
| Dataset | Suitable for experimentation | Synthetic data is useful for development but cannot establish real-world safety performance. |
| Models | Functional hybrid design | Saved model plus hand-built factor score; training reproducibility needs work. |
| Backend | Understandable Flask API | Routing and scoring are separated into routes and services, but dependencies and validation are incomplete. |
| Frontend | Usable demonstration UI | Map and comparison views are present, but the response contract is implicit and error/loading states are limited. |
| Integration | Works conceptually | External OSRM, OpenStreetMap tiles, local model files, and hard-coded API URL create operational dependencies. |
| Production readiness | Not ready | Security, privacy, monitoring, testing, model governance, and reliability controls are missing. |

### Highest-priority findings

1. `Backend/requirements.txt` is empty even though the backend imports Flask, Flask-CORS, pandas, requests, joblib, and a serialized model stack.
2. There are two apparent project trees: the top-level implementation and a nested `ML_CP/` copy. The active copy must be identified and the duplicate removed or explicitly documented.
3. The saved model, scaler, and label encoder are binary artifacts without a recorded feature schema, package versions, training configuration, or model metrics in the repository.
4. The backend runs Flask in debug mode and enables unrestricted CORS, which is unsuitable for deployment.
5. The application presents model confidence as a user-facing percentage, but there is no evidence that the probabilities are calibrated.
6. Route scoring samples only seven geometry points for long routes and uses nearest dataset records. This can miss localized hazards and can reuse the same record for unrelated points.
7. The UI labels the highest-scoring OSRM alternative as “Safest”, but the underlying route generator is still a general driving router, not a safety-aware router.

## 2. Repository and Architecture

### Main areas

| Folder | Role |
|---|---|
| `Backend/` | Flask application, blueprints, and prediction/routing services. |
| `data/` | Synthetic source dataset and train/test CSV files. |
| `models/` | Serialized model, scaler, and label encoder. |
| `frontend/` | React/Vite client, Leaflet map, form, results page, and API wrapper. |
| `notebooks/` | EDA, preprocessing, model training/evaluation, SHAP, and route recommendation work. |
| `scripts/` | Currently empty at the top level. |
| `ML_CP/` | Apparent nested duplicate containing another copy of the project. |

The backend follows a reasonable small-service structure:

```text
Flask app
  -> blueprints/routes
       -> services
            -> CSV and model artifacts
            -> OSRM HTTP API
```

The frontend flow is:

```text
RouteForm
  -> services/api.js
       -> Flask /safe-routes
            -> OSRM alternatives + safety scoring
  -> App state
       -> MapView and route comparison cards
```

### Important repository concerns

- The workspace contains both `Backend/`, `data/`, `frontend/`, `models/`, and `notebooks/` at the root and a nested `ML_CP/` directory with the same broad structure.
- The nested frontend includes `node_modules`, which should normally be excluded from version control and recreated from `package-lock.json`.
- The root and nested copies should be compared and consolidated. Otherwise teammates can edit one copy while running another.
- There is no root-level README that explains which copy is canonical, how to install dependencies, or how to run the complete system.

## 3. Dataset Review

### Dataset role

The backend reads `data/Synthetic_Dataset.csv` at runtime for locations, coordinates, segment safety information, and nearest-record matching. The training workflow also uses `X_train.csv`, `X_test.csv`, `y_train.csv`, and `y_test.csv`.

### Feature groups

The code and notebooks show the following feature groups:

| Group | Fields or examples | Use |
|---|---|---|
| Route identity | `Source`, `Destination` | Identifies an origin-destination pair. |
| Coordinates | `Source_Lat`, `Source_Lon`, `Dest_Lat`, `Dest_Lon` | Resolves locations and matches route points. |
| Time | `Hour` | Selects the closest available time record and feeds the model. |
| Place type | `Source_Type`, `Dest_Type` | Describes endpoint context. |
| Road context | `Road_Type`, `Road_Condition`, `Road_Distance_km` | Describes road quality and length. |
| Environment | `Season`, `Weather`, `Visibility` | Captures environmental conditions. |
| Activity | `Crowd_Density`, `Vehicle_Traffic`, `Pedestrian_Traffic`, `Shops_Open`, `Public_Transport` | Represents presence, activity, and access to help. |
| Safety infrastructure | `Street_Lighting`, `CCTV`, `Emergency_Booth`, `Police_Distance_km` | Represents protective infrastructure and proximity to support. |
| Crime | `Crime_Rate`, `Crime_Probability`, `Theft_Reports`, `Harassment_Reports` | Represents historical or synthetic risk signals. |
| Targets | `Safety_Score`, `Safety_Level` | Used by runtime scoring and supervised learning. |

### Strengths

- The dataset captures multiple factors relevant to the stated problem instead of using distance alone.
- It includes both numerical and categorical variables, which provides a useful classification exercise.
- Separate train/test CSVs make the intended training/evaluation split visible.
- Coordinates allow the ML layer to be connected to a map and route geometry.

### Dataset limitations and risks

1. The dataset is explicitly synthetic. Results cannot be interpreted as evidence that a real location is safe or unsafe.
2. The repository does not document how the synthetic values were generated, whether the target was derived from the same factors, or what assumptions were used.
3. `Source` and `Destination` are included as categorical model features. This can let the model memorize known location pairs instead of learning transferable safety relationships.
4. The runtime uses the nearest `Hour` record rather than a continuous time model or a clearly defined time-window aggregation.
5. Coordinate matching uses the first source or destination row for a location. If a location occurs with different coordinates, the selected coordinate is arbitrary.
6. `find_nearest_records` compares latitude and longitude differences as plain squared degrees. This is not a physical distance calculation and becomes less meaningful over larger areas.
7. The route-point method can select records from a different source-destination pair merely because their endpoint coordinates are close.
8. No data validation, schema validation, missing-value policy, outlier policy, or versioned data contract is visible.
9. There is no evidence of geographic or temporal holdout validation. Random row splitting can overstate performance when nearby or repeated route pairs occur in both train and test data.

### Dataset recommendations

- Add a data dictionary with units, allowed values, provenance, target definition, and synthetic-generation rules.
- Add a validation script that checks columns, types, ranges, missing values, duplicate keys, and category values.
- Split evaluation by route pair or geographic area, not only by random rows.
- Replace categorical endpoint memorization with engineered spatial/context features where generalization matters.
- Use a real, legally obtained, anonymized, and bias-audited safety dataset before making user-facing safety claims.
- Version datasets and model artifacts together using a manifest containing hashes and creation dates.

## 4. Models and Scoring Logic

### Training workflow

The notebooks cover:

1. EDA in `notebooks/01_EDA.ipynb`.
2. Preprocessing in `notebooks/02_Preprocessing.ipynb`.
3. Decision Tree, Random Forest, XGBoost, and LightGBM experiments in `notebooks/03_Model_Training.ipynb`.
4. Metric and confusion-matrix evaluation in `notebooks/04_Model_Evaluation.ipynb`.
5. SHAP exploration in `notebooks/05_Explainable_AI_SHAP.ipynb`.
6. Route recommendation work in `notebooks/06_Route_Recommendation.ipynb`.

The runtime loads:

- `models/best_model.pkl`
- `models/scaler.pkl`
- `models/label_encoder.pkl`

### Runtime prediction path

For `/safe-routes`, the backend:

1. Resolves source and destination coordinates from the CSV.
2. Calls OSRM with `alternatives=3`, full geometry, and GeoJSON coordinates.
3. Samples at most seven route points for each alternative.
4. Finds five nearby dataset records for each sample point.
5. One-hot encodes categorical values and reindexes columns to `scaler.feature_names_in_`.
6. Applies the saved scaler and model.
7. Computes a safety score for each nearby record.
8. Calculates a weighted point score, then combines route average and median.
9. Penalizes confidence when sampled scores vary.
10. Sorts routes by score and labels them `Safest`, `Alternative`, or `Higher Risk`.

### Hybrid score

The service combines the model output and a rule-based factor score:

```text
final_score = 0.70 * ml_score + 0.30 * factor_score
```

The rule-based score begins at 100 and adjusts for crime probability, theft, harassment, lighting, CCTV, emergency booths, police distance, crowd density, shops, public transport, visibility, weather, road condition, and night-time travel. The result is clipped to the range 0 to 100.

### Strengths

- The model artifacts are loaded once at service import time, which avoids reloading them for every request.
- Runtime feature alignment through `scaler.feature_names_in_` reduces one common inference failure: mismatched one-hot columns.
- The hybrid score makes domain rules visible instead of hiding all decisions in the classifier.
- The notebooks include multiple model families and SHAP exploration, which is a good foundation for comparison and explainability.
- Route scores account for both average conditions and median conditions, reducing the effect of a single extreme point.

### Model risks and correctness concerns

1. Training metrics are not stored in a report or CI artifact. Teammates cannot tell which model is “best” or whether the saved model matches the documented experiment.
2. The runtime assumes the serialized model supports `predict_proba`, `n_features_`, and the same label encoding used during training.
3. The model is loaded with `joblib`, which should only load trusted artifacts. Artifact provenance and integrity checks are absent.
4. The model’s probability maximum is shown as “confidence”. A classifier probability is not automatically calibrated confidence.
5. The hybrid weights `0.70` and `0.30`, thresholds 70/45, and factor penalties are hard-coded and not justified by validation.
6. The model predicts safety labels for records selected by geographic proximity, not necessarily the exact road segment represented by the OSRM geometry.
7. Long routes are reduced to seven samples. A short but dangerous section between samples can be missed.
8. The score is based on safety data but the actual route optimization objective is not distance/time/safety multi-objective optimization; it is ranking OSRM alternatives.
9. `predict_complete_route` in `prediction_service.py` expects a `path` of named locations, while the current safe-route workflow uses route geometry and `safe_route_service.py`. These are two partially overlapping prediction approaches that increase maintenance cost.
10. SHAP notebook code contains hard-coded label mappings and assumes a particular SHAP output shape. The explanation pipeline is not exposed through the API and is not tied to the exact user route response.

### Model recommendations

- Add a reproducible training script or pipeline that creates preprocessing, model, encoder, and metrics as one versioned artifact.
- Store model metadata: training data hash, feature list, package versions, model class, label order, metrics, and calibration results.
- Evaluate class-specific recall, especially recall for unsafe routes, alongside weighted averages.
- Calibrate probabilities and rename the UI field if it remains a prediction probability rather than validated confidence.
- Tune hybrid weights and thresholds on a validation set; do not choose them only by intuition.
- Use route-level and geographic holdouts to test generalization.
- Replace nearest-record lookup with a spatial index and map-matched road-segment data where possible.
- Add uncertainty and data-coverage indicators so a sparse or out-of-distribution route is not presented with false precision.
- Add an explainable-AI route rationale feature: calculate route-level SHAP contributions and readable safety-factor reasons, then expose them through the API so the frontend can explain why the selected route ranked highest.

## 5. Backend Review

### API surface

| Endpoint | Method | Purpose |
|---|---|---|
| `/` | GET | Health-style response containing project status. |
| `/locations` | GET | Returns unique source and destination names from the CSV. |
| `/coordinates?location=...` | GET | Returns the first matching coordinate for a location. |
| `/find-route` | POST | Returns one OSRM route for source and destination. |
| `/predict-route` | POST | Uses a named path and predicts segment safety. |
| `/safe-routes` | POST | Retrieves up to three OSRM alternatives and ranks them by sampled safety. |

### Backend strengths

- Flask blueprints separate endpoint groups cleanly.
- Route handlers perform basic required-field validation.
- The services isolate CSV access, OSRM calls, and prediction logic from HTTP handlers.
- OSRM requests use timeouts, preventing an indefinitely blocked request.
- The response includes score, risk level, confidence, geometry, distance, estimated time, and safety details needed by the UI.

### Backend issues

- `Backend/requirements.txt` is empty. A fresh environment cannot be installed reliably from the repository.
- `CORS(app)` allows all origins. Restrict this to the deployed frontend origin.
- `debug=True` is enabled in the application entry point. Disable it outside local development.
- Exceptions are returned as `str(error)`, which may leak internal paths or implementation details.
- `request.get_json()` may return `None`; calling `.get()` then produces a server error instead of a clean 400 response.
- Time validation only checks truthiness. Invalid values such as malformed strings can fail later in `split` or `int`.
- CSV files are re-read at import or request time in several services. This increases startup/request cost and creates inconsistent loading patterns.
- External OSRM and OpenStreetMap services are treated as always available. There is no retry policy, cache, provider fallback, or user-facing degraded mode.
- There is no rate limiting, authentication, request size limit, structured logging, tracing, or health check for model/data readiness.
- There is no API schema or generated client contract. The frontend and backend rely on matching undocumented object shapes.
- The API exposes model-derived safety judgments without a disclaimer, provenance, timestamp, or freshness indicator.

### Backend recommendations

- Populate requirements with pinned compatible versions and document the Python version.
- Add an application factory, environment-based configuration, and a production WSGI command.
- Add centralized validation and error handling with stable error codes.
- Cache immutable dataset/model objects and load them through a single repository module.
- Add `/health/live` and `/health/ready` endpoints that verify model and dataset availability.
- Restrict CORS, add request timeouts and retries for external calls, and cache route responses where appropriate.
- Define response schemas with OpenAPI or Pydantic-style validation.
- Add unit tests for scoring, route ranking, malformed input, missing locations, OSRM failures, and empty nearest-record results.

## 6. Frontend Review

### User flow

1. `RouteForm` loads locations from `/locations`.
2. It initializes the first two locations as default source and destination.
3. The user selects source, destination, and time.
4. `App.jsx` calls `getSafeRoutes` from `services/api.js`.
5. The result page shows the recommended route, alternatives, score, risk level, confidence, route statistics, safety factors, and map.
6. `MapView` separately loads source/destination coordinates and renders the returned route geometries with Leaflet.

### Frontend strengths

- The primary workflow is simple and easy to demonstrate.
- The map uses Leaflet and displays source/destination markers and route polylines.
- Route alternatives are visually distinguished by score/risk and color.
- The layout includes responsive breakpoints for narrower screens.
- The API wrapper centralizes fetch calls instead of scattering requests through every component.

### Frontend issues

1. `BASE_URL` is hard-coded to `http://127.0.0.1:5000`; deployment and teammate environments need an environment variable.
2. The UI uses `alert`, `console.log`, and `console.error` for user feedback and diagnostics. A visible error panel and accessible status should replace these in the main workflow.
3. The location-loading failure is only logged, leaving the user with empty selectors and no explanation.
4. The result view assumes route fields exist. Partial or malformed backend responses can render empty or misleading values.
5. The app reads only the first safety detail to populate the Safety Factors card, even though the backend returns multiple sampled safety details. This does not summarize the full route.
6. The frontend includes `RoutePolyline.jsx`, but the active `MapView` draws backend route geometry directly. The unused component and unused routing dependencies should be removed or integrated deliberately.
7. `react-leaflet-routing-machine` and `leaflet-routing-machine` are declared but the active implementation calls the backend/OSRM path directly.
8. The default Vite `index.css` remains and conflicts conceptually with the application styles, including default dark-mode behavior and a fixed `#root` width.
9. The navbar component uses inline styles while `App.css` contains navbar class styles that are not used by that component.
10. The map has a hard-coded initial center in Pune, so the initial view is not driven by the selected locations until route data is available.
11. No keyboard/accessibility review is visible: labels, alerts, map status, focus states, and color-only route distinctions need explicit attention.
12. There are no frontend tests or end-to-end tests for the route form, loading state, API errors, or rendering a result.

### Frontend recommendations

- Use `VITE_API_BASE_URL` and document it in `.env.example`.
- Add explicit idle/loading/success/error states and disable submission while requests are active.
- Validate source, destination, and time before making the request, including a strict `HH:mm` check.
- Define TypeScript types or runtime schemas for API responses.
- Show a route-level factor summary rather than only the first sampled point.
- Remove unused route components/dependencies or make them part of the chosen architecture.
- Replace default Vite styling with one coherent application stylesheet and verify mobile map/panel behavior.
- Add unit tests and an end-to-end happy-path test with a mocked backend.

## 7. Backend and Frontend Integration

### Current contract

The main client call is:

```json
{
  "source": "...",
  "destination": "...",
  "time": "18:00"
}
```

The `/safe-routes` response is shaped approximately as:

```json
{
  "source": "...",
  "destination": "...",
  "time": "18:00",
  "routes": [
    {
      "route_type": "Safest",
      "safety_score": 78.4,
      "risk_level": "Safe",
      "confidence": 84.1,
      "distance_km": 4.2,
      "estimated_time_minutes": 12,
      "geometry": [[18.52, 73.85]],
      "safety_details": []
    }
  ]
}
```

The coordinate convention is handled correctly at the main boundary: OSRM returns `[longitude, latitude]`, the backend converts it to `[latitude, longitude]`, and Leaflet receives the latter format.

### Integration risks

- The contract is not documented or validated, so a backend rename can silently break cards or map rendering.
- The frontend requests coordinates separately from the route request, producing extra calls and possible race conditions when selections change quickly.
- The frontend and backend both know details of the safety response. A shared schema would reduce drift.
- The application depends on three runtime data sources: local CSV, local model files, and external OSRM/tile services. A failure in any one can make the main experience incomplete.
- The route result does not include score methodology, model version, data timestamp, or a safety disclaimer, which are important for a safety-sensitive interface.

### Recommended integration contract

Define and version a response object with:

- `request_id` and `generated_at`.
- `model_version` and `data_version`.
- `route_source` and `route_provider_status`.
- `score`, `risk_level`, and calibrated `probability` with clear definitions.
- `distance_km`, `duration_minutes`, and `geometry`.
- `factor_summary` aggregated over the route.
- `coverage` or `uncertainty` describing how much of the route had matching safety data.
- Stable error codes for validation, location, routing-provider, model, and internal failures.

## 8. Testing and Quality Review

### Present evidence

- `Backend/test_model.py` checks artifact paths and prints model, scaler, and label-encoder information.
- The notebooks contain exploratory evaluations and plots.
- The frontend provides a `build` and `lint` script through `package.json`.

### Missing coverage

- No automated backend test suite is visible for API behavior.
- No tests cover the hybrid score or route ranking edge cases.
- No regression test verifies the serialized artifacts against the current feature schema.
- No test verifies that the frontend handles empty routes, OSRM errors, invalid input, or malformed safety details.
- No integration test starts Flask and exercises the React client contract.
- No recorded benchmark verifies latency for multiple routes and sampled points.

### Suggested test levels

1. Unit-test factor scoring with fixed rows and expected scores.
2. Unit-test model feature preparation against the scaler feature list.
3. Mock OSRM and test route sorting, route labels, and provider failures.
4. Test API validation for missing JSON, missing fields, invalid time, same endpoints, and unknown locations.
5. Run a frontend component test for form submission, loading, error, and result rendering.
6. Add a mocked end-to-end test for the complete user journey.
7. Add a smoke test that loads the real model artifacts and predicts one known fixture.

### Verification performed during this review

- The frontend production build succeeds with `npm run build`.
- Workspace diagnostics report no errors for this review document.
- `Backend/test_model.py` finds all three artifact files but fails while loading `best_model.pkl` because the current interpreter does not have `lightgbm` installed.
- A broad `compileall` run also traverses the checked-in `Backend/venv`; several installed packages use syntax newer than the current Python 3.11 interpreter. Compilation should be run against project source only, and the virtual environment should not be committed.
- The top-level and nested `Backend/app.py` files are currently identical, while both requirements files are empty.

## 9. Privacy, Safety, and Responsible-Use Considerations

Because this system makes safety-related recommendations for women traveling, technical correctness is not enough. The product should:

- Clearly state that scores are estimates and not guarantees of safety.
- Avoid exposing personally identifying travel history unless it is explicitly required and protected.
- Avoid storing source/destination/time requests by default; if analytics are needed, minimize and anonymize them.
- Explain that synthetic or stale data may not reflect current local conditions.
- Avoid wording that places responsibility on a user for choosing a route that later proves unsafe.
- Validate the system for unequal error rates across locations, times, and user-relevant contexts.
- Include emergency guidance and links to local emergency services rather than presenting the route tool as a substitute for help.
- Treat “Safe” as a model category, not a guarantee. Prefer language such as “lower predicted risk” in product copy.

## 10. Recommended Development Roadmap

### Phase 1: Make the prototype reproducible

- Consolidate the duplicate project tree and declare the canonical root.
- Populate and pin `Backend/requirements.txt`.
- Add root and backend/frontend setup documentation.
- Add `.gitignore` entries for virtual environments, `node_modules`, caches, and local environment files.
- Record model metadata, feature schema, metrics, and artifact hashes.

### Phase 2: Stabilize the contract

- Add strict input/output schemas and stable error codes.
- Centralize dataset/model loading.
- Add backend unit/API tests and a frontend integration test.
- Move the frontend API URL to environment configuration.
- Add proper loading, error, empty-result, and provider-unavailable states.

### Phase 3: Improve safety validity

- Document and audit synthetic data generation.
- Evaluate with geographic and route-level holdouts.
- Calibrate probabilities and measure unsafe-route recall. **Partially addressed only in naming:** the API now adds `predicted_probability` and a confidence note, but probabilities are not yet calibrated.
- Add coverage and uncertainty reporting. **Not yet implemented.**
- Replace nearest-record lookup with map-matched road-segment safety data. **Not yet implemented.**
- Explainable route selection is now implemented for the prototype path. `/safe-routes` returns an `explanation` object for each route with `ml_explanations`, `positive_factors`, `negative_factors`, `risk_factors`, `rule_based_explanations`, and `route_comparison_reason`.
- The backend attempts SHAP explanations against the saved LightGBM model, aggregates contributions across sampled route points, and falls back to rule-based safety checks if SHAP is unavailable or fails. The frontend displays "Why this route was selected", factors improving/reducing the prediction, rule-based safety checks, fallback status, and comparison against alternatives.
- Explanation fidelity now has focused backend coverage: tests check SHAP fallback, route sorting, and that the selected route's explanation belongs to the selected route. This is useful regression coverage, but not a formal explanation-audit framework.

### Phase 4: Build actual safety-aware routing

- Represent the road network as a graph.
- Attach time-aware safety features to road segments.
- Define a transparent cost function combining safety, duration, distance, and user preferences.
- Generate candidate paths and optimize the cost function rather than only ranking generic OSRM alternatives.
- Validate route recommendations with domain experts and carefully designed offline scenarios.

### Phase 5: Production hardening

- Disable debug mode and restrict CORS.
- Add authentication/authorization if user accounts or stored trips are introduced.
- Add monitoring, rate limits, request tracing, provider fallback, and alerting.
- Package the backend with a production WSGI server and a repeatable deployment process.
- Establish model/data refresh, rollback, incident response, and responsible-use review processes.

## 11. Final Conclusion

SafePath AI has a coherent demonstration story and a useful separation between the ML work, backend services, and frontend presentation. The strongest technical contribution is the hybrid route scoring idea: a learned safety prediction is combined with interpretable factors and displayed against route geometry.

The project is not yet ready to claim that it finds objectively safe routes. Today it finds up to three general driving routes from OSRM and ranks them using synthetic, sampled safety estimates. The next engineering priority should be reproducibility and correctness: consolidate the repository, document dependencies and model metadata, formalize the API contract, add tests, and make the scoring limitations visible. The next research priority should be validating the data and building a genuinely safety-aware graph-based routing method.
