import unittest

from app import Registration, create_app, db


class WorkshopSiteTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(
            {
                "TESTING": True,
                "WTF_CSRF_ENABLED": False,
                "SQLALCHEMY_DATABASE_URI": "sqlite://",
            }
        )
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_home_page_renders_dynamic_workshops(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"From Topic to Research Question", response.data)

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")

    def test_rejects_invalid_registration(self):
        response = self.client.post("/api/registrations", json={})
        self.assertEqual(response.status_code, 422)
        self.assertIn("email", response.get_json()["errors"])

    def test_saves_valid_registration(self):
        response = self.client.post(
            "/api/registrations",
            json={
                "requestType": "Register interest",
                "fullName": "Test Student",
                "email": "student@example.com",
                "workshop": "question",
                "message": "Please share updates.",
                "demoConsent": True,
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["reference"], "FYP-00001")
        with self.app.app_context():
            self.assertEqual(Registration.query.count(), 1)

    def test_csrf_blocks_direct_submission_without_token(self):
        protected_app = create_app(
            {
                "TESTING": True,
                "SQLALCHEMY_DATABASE_URI": "sqlite://",
            }
        )
        response = protected_app.test_client().post(
            "/api/registrations",
            json={"fullName": "No Token"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("session expired", response.get_json()["message"].lower())


if __name__ == "__main__":
    unittest.main()
