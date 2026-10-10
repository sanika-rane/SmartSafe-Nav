from flask import Blueprint, request
from services.coordinate_service import get_coordinates

coordinate_bp = Blueprint(
    "coordinate",
    __name__
)

@coordinate_bp.route("/coordinates", methods=["GET"])
def coordinates():

    location = request.args.get("location")

    return get_coordinates(location)