from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFError, CSRFProtect


db = SQLAlchemy()
csrf = CSRFProtect()


WORKSHOPS = [
    {
        "slug": "question",
        "example_session": {
            "date_time": "7 December, 14:00",
            "duration_minutes": 60,
            "mode": "In person",
            "facilitator_role": "Research Methods Tutor",
            "capacity": 20,
        },
        "stage": "Choosing a topic",
        "prepare": "Bring a broad topic and one constraint you need to work around.",
        "takeaway": "A draft question and a scope checklist.",
        "category": "planning",
        "category_label": "Planning",
        "title": "From Topic to Research Question",
        "summary": "Define a focused problem, test its feasibility, and create a realistic research direction.",
        "card_outcomes": ["Scope a researchable question", "Map objectives and constraints"],
        "description": "A proposed hands-on session for turning a broad topic into a focused and feasible research question.",
        "outcomes": [
            "Clarify the problem your project will address",
            "Test scope against time and available resources",
            "Connect the question to practical research objectives",
        ],
        "date": "To be confirmed",
        "time": "To be confirmed",
        "format": "To be confirmed",
        "status": "Preview",
    },
    {
        "slug": "sources",
        "example_session": {
            "date_time": "9 December, 15:00",
            "duration_minutes": 60,
            "mode": "Online",
            "facilitator_role": "Academic Skills Librarian",
            "capacity": 24,
        },
        "stage": "Reviewing literature",
        "prepare": "Bring a draft question or two keywords you have already tried.",
        "takeaway": "A search plan and criteria for checking sources.",
        "category": "evidence",
        "category_label": "Evidence",
        "title": "Finding and Evaluating Sources",
        "summary": "Build a search strategy and judge whether academic sources are relevant, credible, and useful.",
        "card_outcomes": ["Search with stronger keywords", "Evaluate and organise sources"],
        "description": "A proposed session for building a more deliberate literature-search and source-evaluation process.",
        "outcomes": [
            "Develop keyword and database search combinations",
            "Distinguish relevance from credibility",
            "Create an organised evidence trail for later writing",
        ],
        "date": "To be confirmed",
        "time": "To be confirmed",
        "format": "To be confirmed",
        "status": "Preview",
    },
    {
        "slug": "data",
        "example_session": {
            "date_time": "11 December, 14:00",
            "duration_minutes": 75,
            "mode": "In person",
            "facilitator_role": "Data Skills Tutor",
            "capacity": 20,
        },
        "stage": "Planning a method",
        "prepare": "Bring your question and a short description of the evidence you can access.",
        "takeaway": "A question-to-evidence map and notes on responsible data handling.",
        "category": "evidence",
        "category_label": "Evidence",
        "title": "Working with Data and Evidence",
        "summary": "Connect research methods to the evidence needed for a defensible answer.",
        "card_outcomes": ["Match methods to questions", "Plan ethical data handling"],
        "description": "A proposed session for matching research questions with suitable forms of data and analysis.",
        "outcomes": [
            "Identify the evidence needed to answer a question",
            "Compare possible collection and analysis methods",
            "Plan for ethical and careful data handling",
        ],
        "date": "To be confirmed",
        "time": "To be confirmed",
        "format": "To be confirmed",
        "status": "Preview",
    },
    {
        "slug": "writing",
        "example_session": {
            "date_time": "14 December, 15:00",
            "duration_minutes": 60,
            "mode": "Online",
            "facilitator_role": "Writing and Presentation Coach",
            "capacity": 24,
        },
        "stage": "Writing or presenting",
        "prepare": "Bring a draft outline or the finding you want to explain.",
        "takeaway": "A revised outline or a short plan for presenting a finding.",
        "category": "communication",
        "category_label": "Communication",
        "title": "Writing and Presenting the FYP",
        "summary": "Shape a clear argument and present research decisions with confidence.",
        "card_outcomes": ["Structure the research story", "Prepare concise visuals"],
        "description": "A proposed session for shaping a clear research narrative across the report and presentation.",
        "outcomes": [
            "Build a logical section-level argument",
            "Explain methods and findings with precision",
            "Design concise visuals that support the spoken presentation",
        ],
        "date": "To be confirmed",
        "time": "To be confirmed",
        "format": "To be confirmed",
        "status": "Preview",
    },
]

WORKSHOP_BY_SLUG = {workshop["slug"]: workshop for workshop in WORKSHOPS}
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_type = db.Column(db.String(30), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(254), nullable=False)
    workshop_slug = db.Column(db.String(40), nullable=False, index=True)
    message = db.Column(db.String(500), nullable=False, default="")
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


def normalise_database_url(value: str) -> str:
    if value.startswith("postgres://"):
        return value.replace("postgres://", "postgresql+psycopg://", 1)
    if value.startswith("postgresql://"):
        return value.replace("postgresql://", "postgresql+psycopg://", 1)
    return value


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    default_database = f"sqlite:///{Path(app.instance_path) / 'workshops.db'}"
    database_url = normalise_database_url(os.getenv("DATABASE_URL", default_database))
    on_render = os.getenv("RENDER") == "true"
    secret_key = os.getenv("SECRET_KEY", "").strip()
    if on_render and (len(secret_key) < 32 or secret_key == "replace-with-a-long-random-value"):
        raise RuntimeError("Set a random SECRET_KEY of at least 32 characters in Render Environment.")

    app.config.from_mapping(
        SECRET_KEY=secret_key or "development-only-change-me",
        SESSION_COOKIE_SECURE=on_render,
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        GA4_MEASUREMENT_ID=os.getenv("GA4_MEASUREMENT_ID", "").strip(),
        MAX_CONTENT_LENGTH=16 * 1024,
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    csrf.init_app(app)

    with app.app_context():
        db.create_all()

    @app.get("/")
    def index():
        workshop_data = {
            item["slug"]: {
                "category": item["category_label"],
                "title": item["title"],
                "description": item["description"],
                "outcomes": item["outcomes"],
                "prepare": item["prepare"],
                "takeaway": item["takeaway"],
                "example_session": item["example_session"],
            }
            for item in WORKSHOPS
        }
        return render_template(
            "index.html",
            workshops=WORKSHOPS,
            workshop_data=workshop_data,
            ga4_id=app.config["GA4_MEASUREMENT_ID"] if re.fullmatch(
                r"G-[A-Z0-9]+", app.config["GA4_MEASUREMENT_ID"]
            ) else None,
        )

    @app.get("/api/workshops")
    def list_workshops():
        return jsonify({"workshops": WORKSHOPS})

    @app.post("/api/registrations")
    def create_registration():
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify({"message": "Send the form as JSON."}), 400

        errors = validate_registration(payload)
        if errors:
            return jsonify({"message": "Please correct the highlighted fields.", "errors": errors}), 422

        registration = Registration(
            request_type=payload["requestType"].strip(),
            full_name=payload["fullName"].strip(),
            email=payload["email"].strip().lower(),
            workshop_slug=payload["workshop"].strip(),
            message=payload.get("message", "").strip(),
        )
        db.session.add(registration)
        db.session.commit()

        workshop = WORKSHOP_BY_SLUG[registration.workshop_slug]
        return (
            jsonify(
                {
                    "message": "Your demonstration entry has been saved.",
                    "reference": f"FYP-{registration.id:05d}",
                    "workshop": workshop["title"],
                    "requestType": registration.request_type,
                }
            ),
            201,
        )

    @app.get("/health")
    def health():
        db.session.execute(db.select(Registration.id).limit(1)).first()
        return jsonify({"status": "ok", "database": "connected"})

    @app.errorhandler(CSRFError)
    def handle_csrf_error(error: CSRFError):
        if request.path.startswith("/api/"):
            return jsonify({"message": "Your session expired. Refresh the page and try again."}), 400
        return error.description, 400

    @app.errorhandler(413)
    def request_too_large(_error):
        return jsonify({"message": "The submitted form is too large."}), 413

    return app


def validate_registration(payload: dict) -> dict[str, str]:
    errors: dict[str, str] = {}
    request_type = str(payload.get("requestType", "")).strip()
    full_name = str(payload.get("fullName", "")).strip()
    email = str(payload.get("email", "")).strip()
    workshop = str(payload.get("workshop", "")).strip()
    message = str(payload.get("message", "")).strip()

    if request_type not in {"Register interest", "Make an enquiry"}:
        errors["requestType"] = "Choose a valid request type."
    if not 2 <= len(full_name) <= 100:
        errors["fullName"] = "Enter a name between 2 and 100 characters."
    if len(email) > 254 or not EMAIL_PATTERN.fullmatch(email):
        errors["email"] = "Enter a valid email address."
    if workshop not in WORKSHOP_BY_SLUG:
        errors["workshop"] = "Choose a valid workshop."
    if len(message) > 500:
        errors["message"] = "Keep the note within 500 characters."
    if payload.get("demoConsent") is not True:
        errors["demoConsent"] = "Confirm that you understand how this demonstration stores your entry."
    return errors


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5050")), debug=True)
