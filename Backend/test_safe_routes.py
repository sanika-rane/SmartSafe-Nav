import unittest
from unittest.mock import patch

import pandas as pd

from app import app
from services import safe_route_service


class SafeRouteApiTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_health_endpoint(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "Running")

    def test_locations_response(self):
        response = self.client.get("/locations")

        self.assertEqual(response.status_code, 200)
        self.assertIn("locations", response.get_json())

    def test_missing_json_body(self):
        response = self.client.post("/safe-routes")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["code"], "missing_json")

    def test_missing_source(self):
        response = self.client.post(
            "/safe-routes",
            json={
                "destination": "Baner",
                "time": "18:00",
            }
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["code"], "missing_source")

    def test_missing_destination(self):
        response = self.client.post(
            "/safe-routes",
            json={
                "source": "Kothrud",
                "time": "18:00",
            }
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["code"], "missing_destination")

    def test_missing_time(self):
        response = self.client.post(
            "/safe-routes",
            json={
                "source": "Kothrud",
                "destination": "Baner",
            }
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["code"], "missing_time")

    def test_invalid_time(self):
        response = self.client.post(
            "/safe-routes",
            json={
                "source": "Kothrud",
                "destination": "Baner",
                "time": "25:00",
            }
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["code"], "invalid_time")

    def test_same_source_and_destination(self):
        response = self.client.post(
            "/safe-routes",
            json={
                "source": "Kothrud",
                "destination": "kothrud",
                "time": "18:00",
            }
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json()["code"],
            "same_source_destination"
        )

    @patch("routes.safe_route_routes.find_safest_routes")
    def test_unknown_location(self, mock_find):
        mock_find.return_value = {
            "error": "Unknown location: Atlantis",
            "code": "unknown_location",
            "status_code": 404,
        }

        response = self.client.post(
            "/safe-routes",
            json={
                "source": "Atlantis",
                "destination": "Baner",
                "time": "18:00",
            }
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json()["code"], "unknown_location")

    @patch("routes.safe_route_routes.find_safest_routes")
    def test_mocked_osrm_success(self, mock_find):
        mock_find.return_value = {
            "source": "Kothrud",
            "destination": "Baner",
            "time": "18:00",
            "routes": [
                {
                    "route_type": "Safest",
                    "safety_score": 82,
                    "explanation": {
                        "summary": "Mock explanation"
                    },
                }
            ],
        }

        response = self.client.post(
            "/safe-routes",
            json={
                "source": "Kothrud",
                "destination": "Baner",
                "time": "18:00",
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json()["routes"][0]["route_type"],
            "Safest"
        )

    @patch("routes.safe_route_routes.find_safest_routes")
    def test_mocked_osrm_failure(self, mock_find):
        mock_find.return_value = {
            "error": "Routing service is unavailable. Please try again later.",
            "code": "osrm_unavailable",
            "status_code": 503,
        }

        response = self.client.post(
            "/safe-routes",
            json={
                "source": "Kothrud",
                "destination": "Baner",
                "time": "18:00",
            }
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json()["code"], "osrm_unavailable")


class SafeRouteServiceTests(unittest.TestCase):
    def sample_route(self, distance):
        return {
            "distance": distance,
            "duration": 600,
            "geometry": {
                "coordinates": [
                    [73.80, 18.50],
                    [73.81, 18.51],
                ]
            },
        }

    @patch("services.safe_route_service.ensure_runtime_ready")
    @patch("services.safe_route_service.get_osrm_routes")
    @patch("services.safe_route_service.score_route")
    def test_route_sorting_by_safety_score(
        self,
        mock_score,
        mock_osrm,
        mock_ready
    ):
        mock_ready.return_value = None
        mock_osrm.return_value = [
            self.sample_route(1000),
            self.sample_route(2000),
        ]
        mock_score.side_effect = [
            {
                "safety_score": 55,
                "safety_details": [],
                "explanation": {},
            },
            {
                "safety_score": 88,
                "safety_details": [],
                "explanation": {},
            },
        ]

        result = safe_route_service.find_safest_routes(
            "Kothrud",
            "Baner",
            "18:00"
        )

        self.assertEqual(result["routes"][0]["safety_score"], 88)
        self.assertEqual(result["routes"][0]["route_type"], "Safest")

    @patch("services.safe_route_service.get_shap_explainer")
    def test_explanation_fallback_when_shap_unavailable(self, mock_shap):
        mock_shap.return_value = None

        prediction = {
            "scaled_features": [[0]],
            "predicted_class_index": 1,
            "features": pd.DataFrame([{"Crime_Probability": 0.2}]),
        }

        result = safe_route_service.model_contributions(prediction)

        self.assertEqual(result["status"], "fallback")
        self.assertEqual(result["method"], "rule_based_only")

    @patch("services.safe_route_service.ensure_runtime_ready")
    @patch("services.safe_route_service.get_osrm_routes")
    @patch("services.safe_route_service.score_route")
    def test_explanation_belongs_to_selected_route(
        self,
        mock_score,
        mock_osrm,
        mock_ready
    ):
        mock_ready.return_value = None
        mock_osrm.return_value = [
            self.sample_route(1000),
            self.sample_route(2000),
        ]
        mock_score.side_effect = [
            {
                "safety_score": 45,
                "safety_details": [],
                "explanation": {
                    "summary": "Lower route explanation",
                },
            },
            {
                "safety_score": 91,
                "safety_details": [],
                "explanation": {
                    "summary": "Higher route explanation",
                },
            },
        ]

        result = safe_route_service.find_safest_routes(
            "Kothrud",
            "Baner",
            "18:00"
        )

        self.assertEqual(result["routes"][0]["safety_score"], 91)
        self.assertNotEqual(
            result["routes"][0]["explanation"]["summary"],
            "Lower route explanation"
        )

    def test_model_feature_preparation_matches_scaler_feature_names(self):
        class FakeScaler:
            feature_names_in_ = [
                "Crime_Probability",
                "CCTV_Yes",
                "Street_Lighting_High",
            ]

        previous_scaler = safe_route_service._scaler
        previous_model = safe_route_service._model
        previous_label = safe_route_service._label_encoder
        previous_dataset = safe_route_service._dataset
        previous_load_error = safe_route_service._load_error

        safe_route_service._scaler = FakeScaler()
        safe_route_service._model = object()
        safe_route_service._label_encoder = object()
        safe_route_service._dataset = pd.DataFrame([{}])
        safe_route_service._load_error = None

        try:
            features = safe_route_service.prepare_features(
                pd.Series(
                    {
                        "Crime_Probability": 0.4,
                        "CCTV": "Yes",
                        "Street_Lighting": "High",
                        "Safety_Score": 80,
                        "Safety_Level": "Safe",
                    }
                )
            )
        finally:
            safe_route_service._scaler = previous_scaler
            safe_route_service._model = previous_model
            safe_route_service._label_encoder = previous_label
            safe_route_service._dataset = previous_dataset
            safe_route_service._load_error = previous_load_error

        self.assertEqual(
            list(features.columns),
            FakeScaler.feature_names_in_
        )


if __name__ == "__main__":
    unittest.main()
