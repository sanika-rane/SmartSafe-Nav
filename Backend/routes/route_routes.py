from flask import Blueprint, request, jsonify

from services.route_service import find_route


route_bp = Blueprint(
    "route",
    __name__
)


@route_bp.route(
    "/find-route",
    methods=["POST"]
)
def route():

    try:

        data = request.get_json(silent=True)

        if data is None:

            return jsonify({
                "error": "Request body must be valid JSON.",
                "code": "missing_json"
            }), 400

        source = data.get("source")
        destination = data.get("destination")


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


        result = find_route(
            source,
            destination
        )


        if "error" in result:

            return jsonify(result), 404


        return jsonify(result)


    except Exception:

        return jsonify({
            "error": "Unable to find a route right now.",
            "code": "internal_error"
        }), 500
