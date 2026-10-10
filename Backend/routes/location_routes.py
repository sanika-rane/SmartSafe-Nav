from flask import Blueprint

from services.location_service import get_all_locations

location_bp = Blueprint(
    "location",
    __name__
)


@location_bp.route("/locations", methods=["GET"])
def locations():

    return {
        "locations": get_all_locations()
    }