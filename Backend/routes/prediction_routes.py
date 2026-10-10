from flask import Blueprint, request, jsonify

from services.route_service import find_route
from services.prediction_service import predict_complete_route


prediction_bp = Blueprint(
    "prediction",
    __name__
)


@prediction_bp.route(
    "/predict-route",
    methods=["POST"]
)
def predict_route_api():

    try:

        data = request.get_json(silent=True)

        if data is None:

            return jsonify({
                "error": "Request body must be valid JSON.",
                "code": "missing_json"
            }), 400

        source = data.get("source")

        destination = data.get("destination")

        travel_time = data.get("time")


        if not source:

            return jsonify({
                "error": "Source is required",
                "code": "missing_source"
            }), 400


        if not destination:

            return jsonify({
                "error": "Destination is required",
                "code": "missing_destination"
            }), 400


        if not travel_time:

            return jsonify({
                "error": "Time is required",
                "code": "missing_time"
            }), 400


        # ----------------------------------
        # Find route
        # ----------------------------------

        route = find_route(
            source,
            destination
        )


        if "error" in route:

            return jsonify(route), 404


        # ----------------------------------
        # ML prediction
        # ----------------------------------

        prediction = predict_complete_route(
            route["path"],
            travel_time
        )


        if "error" in prediction:

            return jsonify(prediction), 500


        # ----------------------------------
        # Combine
        # ----------------------------------

        return jsonify({

            "source": source,

            "destination": destination,

            "time": travel_time,

            "path": route["path"],

            "distance_km":
                route["distance_km"],

            "estimated_time_minutes":
                route["estimated_time_minutes"],

            "safety_score":
                prediction["safety_score"],

            "risk_level":
                prediction["risk_level"],

            "confidence":
                prediction["confidence"],

            "segments":
                prediction["segments"]

        })


    except Exception:

        print(
            "Prediction error"
        )

        return jsonify({
            "error": "Unable to predict route right now.",
            "code": "internal_error"
        }), 500
