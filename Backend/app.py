import logging

from flask import Flask
from flask_cors import CORS

from routes.location_routes import location_bp
from routes.coordinate_routes import coordinate_bp
from routes.prediction_routes import prediction_bp
from routes.route_routes import route_bp
from routes.safe_route_routes import safe_route_bp


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)

app = Flask(__name__)

CORS(app)


app.register_blueprint(location_bp)

app.register_blueprint(coordinate_bp)

app.register_blueprint(prediction_bp)

app.register_blueprint(route_bp)

app.register_blueprint(safe_route_bp)


@app.route("/")
def home():

    return {
        "status": "Running",
        "project": "SafePath AI"
    }


if __name__ == "__main__":

    app.run(
        debug=True
    )
