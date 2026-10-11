# UIC FYP Research Workshops Flask Prototype

This project is a dynamic Flask version of the BA4043 case-study website. Workshop content is rendered by Flask, and the registration/enquiry form is validated by the browser and the server before being stored in a database.

## Main features

- Flask-rendered workshop cards, schedule rows, form options, and dialog data
- JSON endpoints for workshop data and registration submission
- SQLite storage for local development
- PostgreSQL support through `DATABASE_URL` for online deployment
- CSRF protection, server-side validation, request-size limits, and generic failure feedback
- Health endpoint at `/health`
- Responsive desktop and mobile interface
- Automated backend tests
- Gunicorn, Procfile, and Docker deployment options

## Project structure

```text
app.py                    Flask app, data model, routes, and validation
templates/index.html      Jinja page template
static/css/styles.css     Responsive visual design
static/js/script.js       Interactions and API submission
static/assets/            Local image assets
tests/test_app.py         Backend tests
requirements.txt          Python dependencies
Procfile                  Gunicorn process command
Dockerfile                Container deployment definition
.env.example              Environment variable example
```

## Run locally

From this project directory:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Open `http://127.0.0.1:5050/`.

The first run creates `instance/workshops.db`. This database is excluded from Git because it can contain submitted names and email addresses.

## Run tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Production configuration

Set these environment variables on the hosting platform:

- `SECRET_KEY`: a long random value; never commit the real value
- `DATABASE_URL`: managed PostgreSQL connection string
- `PORT`: normally supplied by the platform

The production start command is:

```text
gunicorn --bind 0.0.0.0:$PORT app:app
```

For Docker:

```powershell
docker build -t fyp-workshops .
docker run --rm -p 8000:8000 -e SECRET_KEY="replace-me" fyp-workshops
```

## Before public deployment

- Replace proposed workshop information only with verified official details.
- Add an approved privacy notice, retention period, and deletion process.
- Use managed PostgreSQL rather than the default SQLite database.
- Restrict staff access before adding any submission-management page.
- Add database migrations before changing the production schema.
- Configure HTTPS, trusted hosts, monitoring, backups, and platform secrets.
- Confirm institutional approval before collecting real student data.

This remains a student case-study prototype and is not an official UIC registration service.

## Image generation record

The hero image was created with the built-in OpenAI image generation tool. Prompt summary: a wide, documentary-style university research workshop with students collaborating in a modern seminar room, people placed toward the right, clear space for hero copy, no branding, no legible text, and no watermark.
