import { useState } from "react";

import Navbar from "./components/Navbar";
import RouteForm from "./components/RouteForm";
import MapView from "./components/MapView";

import { getSafeRoutes } from "./services/api";


function App() {

  const [source, setSource] = useState("");
  const [destination, setDestination] = useState("");
  const [time, setTime] = useState("18:00");

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");


  /* ========================================
     FIND SAFE ROUTE
  ======================================== */

  async function handleFindRoute() {

    if (!source || !destination) {
      setErrorMessage("Please select source and destination.");
      return;
    }

    if (source === destination) {
      setErrorMessage("Source and destination cannot be the same.");
      return;
    }

    try {

      setLoading(true);
      setErrorMessage("");

      const data = await getSafeRoutes(
        source,
        destination,
        time
      );

      console.log(
        "SAFE ROUTE RESULT:",
        data
      );

      setResult(data);

    } catch (error) {

      console.error(
        "Route error:",
        error
      );

      setErrorMessage(
        error.message ||
        "Unable to find safe routes right now."
      );

    } finally {

      setLoading(false);

    }
  }


  /* ========================================
     BACK TO HOME
  ======================================== */

  function handleBack() {
    setResult(null);
  }


  /* ========================================
     SAFETY VALUE HELPER
  ======================================== */

  function normalizeKey(key) {

    return String(key)
      .toLowerCase()
      .replace(/[\s_-]/g, "")
      .replace(/[^\w]/g, "");

  }


  function findValue(object, possibleKeys) {

    if (!object || typeof object !== "object") {
      return undefined;
    }


    const normalizedObjectKeys =
      Object.keys(object);


    const normalizedPossibleKeys =
      possibleKeys.map(normalizeKey);


    /* ----------------------------------------
       DIRECT KEY MATCH
    ---------------------------------------- */

    for (const key of normalizedObjectKeys) {

      const normalizedKey =
        normalizeKey(key);

      if (
        normalizedPossibleKeys.includes(
          normalizedKey
        )
      ) {

        return object[key];

      }

    }


    /* ----------------------------------------
       RECURSIVE SEARCH
       Handles nested safety objects
    ---------------------------------------- */

    for (const key of normalizedObjectKeys) {

      const value = object[key];

      if (
        value &&
        typeof value === "object" &&
        !Array.isArray(value)
      ) {

        const nestedValue =
          findValue(
            value,
            possibleKeys
          );

        if (
          nestedValue !== undefined &&
          nestedValue !== null
        ) {

          return nestedValue;

        }

      }

    }


    return undefined;

  }


  function getSafetyValue(
    safetyDetails,
    possibleKeys,
    fallback = "N/A"
  ) {

    const value =
      findValue(
        safetyDetails,
        possibleKeys
      );


    if (
      value === undefined ||
      value === null ||
      value === ""
    ) {

      return fallback;

    }


    return value;

  }


  function getExplanation(route) {

    return route?.explanation || {};

  }


  function getExplanationList(
    explanation,
    keys
  ) {

    for (const key of keys) {

      const value = explanation?.[key];

      if (
        Array.isArray(value) &&
        value.length > 0
      ) {

        return value;

      }

    }

    return [];

  }


  function renderFactorList(items, emptyText) {

    if (!items || items.length === 0) {

      return (
        <p className="empty-text">
          {emptyText}
        </p>
      );

    }

    return (
      <ul className="explanation-list">
        {items.map((item, index) => (
          <li key={index}>
            <strong>
              {item.feature || item}
            </strong>
            {item.reason && (
              <span>
                {item.reason}
              </span>
            )}
          </li>
        ))}
      </ul>
    );

  }


  /* ========================================
     FIRST PAGE
  ======================================== */

  if (!result) {

    return (
      <>

        <Navbar />


        <RouteForm
          source={source}
          destination={destination}
          time={time}
          setSource={setSource}
          setDestination={setDestination}
          setTime={setTime}
          onFindRoute={handleFindRoute}
          loading={loading}
          errorMessage={errorMessage}
        />

        {errorMessage && (
          <div className="home-error">
            {errorMessage}
          </div>
        )}


        <div className="home-map">

          <MapView
            source={source}
            destination={destination}
            result={null}
          />

        </div>

      </>
    );

  }


  /* ========================================
     RESULTS DATA
  ======================================== */

  const routes =
    result.routes || [];


  const safestRoute =
    routes.length > 0
      ? routes[0]
      : null;


  const safestDetails =
    safestRoute?.safety_details || [];


  const safestExplanation =
    getExplanation(safestRoute);


  const positiveFactors =
    getExplanationList(
      safestExplanation,
      [
        "positive_factors"
      ]
    );


  const negativeFactors =
    getExplanationList(
      safestExplanation,
      [
        "negative_factors",
        "risk_factors"
      ]
    );


  const ruleBasedFactors =
    getExplanationList(
      safestExplanation,
      [
        "rule_based_explanations",
        "rule_based_factors"
      ]
    );


  /*
     We use the first available safety record
     for the Safety Factors card.
  */

  const firstSafetyDetail =
    Array.isArray(safestDetails)
      ? safestDetails[0] || {}
      : safestDetails || {};


  console.log(
    "SAFETY DETAILS:",
    firstSafetyDetail
  );


  /* ========================================
     SAFETY FACTOR VALUES
  ======================================== */

  const cctv =
    getSafetyValue(
      firstSafetyDetail,
      [
        "CCTV",
        "cctv",
        "CCTV Availability",
        "CCTV_Installed",
        "CCTV_Presence"
      ]
    );


  const lighting =
    getSafetyValue(
      firstSafetyDetail,
      [
        "Street_Lighting",
        "Street Lighting",
        "street_lighting",
        "lighting",
        "Lighting",
        "Lighting_Level"
      ]
    );


  const crimeProbability =
    getSafetyValue(
      firstSafetyDetail,
      [
        "Crime_Probability",
        "Crime Probability",
        "crime_probability",
        "crimeProbability",
        "Crime Probability Score"
      ]
    );


  const policeDistance =
    getSafetyValue(
      firstSafetyDetail,
      [
        "Police_Distance_km",
        "Police Distance km",
        "Police Distance",
        "police_distance_km",
        "police_distance",
        "Police_Distance",
        "policeDistance"
      ]
    );


  const crowdDensity =
    getSafetyValue(
      firstSafetyDetail,
      [
        "Crowd_Density",
        "Crowd Density",
        "crowd_density",
        "crowdDensity",
        "Crowd"
      ]
    );


  const weather =
    getSafetyValue(
      firstSafetyDetail,
      [
        "Weather",
        "weather",
        "Weather Condition",
        "Weather_Condition"
      ]
    );


  /* ========================================
     RESULTS PAGE
  ======================================== */

  return (
    <>

      <Navbar />


      <div className="results-page">


        {/* =================================
            BACK BUTTON
        ================================= */}

        <button
          className="back-button"
          onClick={handleBack}
        >
          ← Back to Route Selection
        </button>


        {/* =================================
            HEADER
        ================================= */}

        <div className="results-header">

          <div className="results-title-row">

            <div>

              <h1>
                Route Safety Analysis
              </h1>

              <p>
                {result.source}
                {" → "}
                {result.destination}
                {" • "}
                Travel time: {result.time}
              </p>

            </div>


            <div className="analysis-status">
              AI Safety Analysis
            </div>

          </div>

        </div>


        {/* =================================
            MAIN CONTENT
        ================================= */}

        <div className="results-layout">


          {/* =================================
              MAP
          ================================= */}

          <div className="results-map-container">

            <div className="results-map">

              <MapView
                source={result.source}
                destination={result.destination}
                result={result}
              />

            </div>


            {/* =================================
                MAP LEGEND
            ================================= */}

            <div className="map-legend">

              <div className="legend-title">
                Route Safety
              </div>


              <div className="legend-items">


                <div className="legend-item">

                  <span
                    className="legend-line safest-line"
                  ></span>

                  <span>
                    Safest Route
                  </span>

                </div>


                <div className="legend-item">

                  <span
                    className="legend-line alternative-line"
                  ></span>

                  <span>
                    Alternative Route
                  </span>

                </div>


                <div className="legend-item">

                  <span
                    className="legend-line moderate-line"
                  ></span>

                  <span>
                    Moderate Risk
                  </span>

                </div>


                <div className="legend-item">

                  <span
                    className="legend-line unsafe-line"
                  ></span>

                  <span>
                    Unsafe Route
                  </span>

                </div>


              </div>

            </div>

          </div>


          {/* =================================
              RIGHT PANEL
          ================================= */}

          <div className="safety-panel">


            {/* =================================
                SAFEST ROUTE CARD
            ================================= */}

            {safestRoute && (

              <div className="safe-card">


                <div className="safe-card-header">

                  <div>

                    <div className="recommended-label">
                      RECOMMENDED ROUTE
                    </div>

                    <h2>
                      Safest Route
                    </h2>

                  </div>


                  <div className="safe-icon">
                    ✓
                  </div>

                </div>


                {/* SAFETY SCORE */}

                <div className="score">

                  {safestRoute.safety_score}

                  <span>
                    /100
                  </span>

                </div>


                {/* RISK LEVEL */}

                <div className="risk">

                  Risk Level

                  <strong>
                    {safestRoute.risk_level}
                  </strong>

                </div>


                {/* CONFIDENCE */}

                <div className="confidence">

                  Predicted Probability

                  <strong>
                    {safestRoute.predicted_probability ?? safestRoute.confidence}%
                  </strong>

                </div>


                <p className="confidence-note">
                  {safestRoute.model_confidence_note ||
                    "This is a model probability, not a guarantee of safety."}
                </p>


                <div className="safe-divider"></div>


                {/* ROUTE STATS */}

                <div className="route-info">


                  <div>

                    <span>
                      Distance
                    </span>

                    <strong>
                      {safestRoute.distance_km} km
                    </strong>

                  </div>


                  <div>

                    <span>
                      Estimated Time
                    </span>

                    <strong>
                      {safestRoute.estimated_time_minutes} min
                    </strong>

                  </div>


                </div>


                {/* ROUTE */}

                <h3>
                  Route
                </h3>


                <div className="route-path">

                  {result.source}
                  {" → "}
                  {result.destination}

                </div>


              </div>

            )}


            {/* =================================
                ROUTE COMPARISON
            ================================= */}

            <div className="route-comparison-card">


              <div className="section-heading">

                <div>

                  <h2>
                    Route Comparison
                  </h2>

                  <p>
                    Compare available routes based on predicted safety
                  </p>

                </div>

              </div>


              <div className="route-options">


                {routes.length === 0 && (

                  <p className="empty-text">
                    No route alternatives were returned.
                  </p>

                )}


                {routes.map(
                  (route, index) => {


                    const routeClass =
                      route.risk_level === "Unsafe"
                        ? "unsafe-route"
                        : route.risk_level === "Moderate"
                        ? "moderate-route"
                        : route.route_type === "Safest"
                        ? "recommended-option"
                        : "alternative-option";


                    return (

                      <div
                        className={`route-option ${routeClass}`}
                        key={index}
                      >


                        {/* ROUTE HEADER */}

                        <div className="route-option-header">


                          <div className="route-option-title">


                            <span className="route-dot">

                              {route.route_type === "Safest"
                                ? "★"
                                : "●"}

                            </span>


                            <strong>
                              {route.route_type}
                            </strong>


                          </div>


                          <span className="route-risk-badge">

                            {route.risk_level}

                          </span>


                        </div>


                        {/* SCORE */}

                        <div className="route-score-row">

                          <span>
                            Safety Score
                          </span>


                          <strong>

                            {route.safety_score}

                            <small>
                              /100
                            </small>

                          </strong>

                        </div>


                        {/* ROUTE STATS */}

                        <div className="route-stats">


                          <div>

                            <span>
                              Distance
                            </span>

                            <strong>
                              {route.distance_km} km
                            </strong>

                          </div>


                          <div>

                            <span>
                              Estimated Time
                            </span>

                            <strong>
                              {route.estimated_time_minutes} min
                            </strong>

                          </div>


                          <div>

                            <span>
                              Confidence
                            </span>

                            <strong>
                              {route.confidence}%
                            </strong>

                          </div>


                        </div>


                      </div>

                    );

                  }
                )}

              </div>

            </div>


            {/* =================================
                SAFETY FACTORS
            ================================= */}

            {safestRoute && (

              <div className="factor-card">


                <div className="section-heading">

                  <div>

                    <h2>
                      Safety Factors
                    </h2>

                    <p>
                      Factors considered by the safety prediction model
                    </p>

                  </div>

                </div>


                <div className="factors">


                  {/* CCTV */}

                  <span>

                    <b>
                      CCTV
                    </b>

                    <br />

                    {cctv}

                  </span>


                  {/* STREET LIGHTING */}

                  <span>

                    <b>
                      Street Lighting
                    </b>

                    <br />

                    {lighting}

                  </span>


                  {/* CRIME PROBABILITY */}

                  <span>

                    <b>
                      Crime Probability
                    </b>

                    <br />

                    {crimeProbability}

                  </span>


                  {/* POLICE DISTANCE */}

                  <span>

                    <b>
                      Police Distance
                    </b>

                    <br />

                    {policeDistance}

                    {policeDistance !== "N/A"
                      ? " km"
                      : ""}

                  </span>


                  {/* CROWD DENSITY */}

                  <span>

                    <b>
                      Crowd Density
                    </b>

                    <br />

                    {crowdDensity}

                  </span>


                  {/* WEATHER */}

                  <span>

                    <b>
                      Weather
                    </b>

                    <br />

                    {weather}

                  </span>


                </div>

              </div>

            )}


          </div>

        </div>


        {safestRoute && (

          <section className="explanation-card" aria-labelledby="why-this-route">

            <div className="section-heading">

              <div>

                <p className="section-kicker">RECOMMENDATION DETAILS</p>

                <h2 id="why-this-route">
                  Why This Route?
                </h2>

                <p>
                  Predicted safety factors for the recommended route
                </p>

              </div>

            </div>


            <p className="explanation-summary">
              {safestExplanation.summary ||
                "This route ranked highest by the final safety score."}
            </p>


            <div className="explanation-status">
              <span>Explanation: {safestExplanation.status ||
                safestExplanation.explanation_status ||
                "available"}</span>
              <span>Method: {safestExplanation.method ||
                safestExplanation.explanation_method ||
                "rule-based"}</span>
            </div>


            <div className="explanation-grid">

              <div className="explanation-section positive-factors">

                <h3>Factors improving the prediction</h3>

                {renderFactorList(
                  positiveFactors,
                  "No positive model factors were returned for this route."
                )}

              </div>


              <div className="explanation-section negative-factors">

                <h3>Factors reducing the prediction</h3>

                {renderFactorList(
                  negativeFactors,
                  "No reducing model factors were returned for this route."
                )}

              </div>


              <div className="explanation-section rule-factors">

                <h3>Rule-based safety checks</h3>

                {renderFactorList(
                  ruleBasedFactors,
                  "No rule-based safety checks were returned."
                )}

              </div>

            </div>


            <div className="explanation-comparison">
              {safestExplanation.comparison ||
                safestExplanation.route_comparison_reason ||
                "Ranked against alternatives by final safety score."}
            </div>

          </section>

        )}

      </div>

    </>
  );
}


export default App;
