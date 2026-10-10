import logging
import re

from flask import Blueprint, request, jsonify

from services.safe_route_service import find_safest_routes
from services.safe_route_service import readiness_status


safe_route_bp = Blueprint(
    "safe_route",
    __name__
)

logger = logging.getLogger(__name__)

TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def json_error(message, status_code, code):
    return jsonify({
        "error": message,
        "code": code
    }), status_code


def validate_safe_route_request(data):
    if data is None:
        return json_error(
            "Request body must be valid JSON.",
            400,
            "missing_json"
        )

    source = str(data.get("source", "")).strip()
    destination = str(data.get("destination", "")).strip()
    travel_time = str(data.get("time", "")).strip()

    if not source:
        return json_error(
            "Source is required.",
            400,
            "missing_source"
        )

    if not destination:
        return json_error(
            "Destination is required.",
            400,
            "missing_destination"
        )

    if not travel_time:
        return json_error(
            "Travel time is required.",
            400,
            "missing_time"
        )

    if not TIME_RE.match(travel_time):
        return json_error(
            "Travel time must use HH:mm format.",
            400,
            "invalid_time"
        )

    if source.casefold() == destination.casefold():
        return json_error(
            "Source and destination cannot be the same.",
            400,
            "same_source_destination"
        )

    return None


@safe_route_bp.route(
    "/model-readiness",
    methods=["GET"]
)
def model_readiness():
    status = readiness_status()
    return jsonify(status), 200 if status["ready"] else 503


@safe_route_bp.route(
    "/safe-routes",
    methods=["POST"]
)
def safe_routes():

    try:

        data = request.get_json(silent=True)

        validation_error = validate_safe_route_request(data)

        if validation_error:
            return validation_error

        source = data["source"].strip()
        destination = data["destination"].strip()
        travel_time = data["time"].strip()

        result = find_safest_routes(
            source,
            destination,
            travel_time
        )

        if "error" in result:

            return jsonify({
                "error": result["error"],
                "code": result.get("code", "safe_route_error")
            }), result.get("status_code", 400)

        return jsonify(result)

    except Exception:

        logger.exception("Unexpected /safe-routes failure")

        return jsonify({
            "error": "Unable to calculate safe routes right now.",
            "code": "internal_error"
        }), 500
