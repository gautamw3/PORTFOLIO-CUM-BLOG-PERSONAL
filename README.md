# Portfolio Cum Blog (Django)

A personal portfolio and blog platform built with Django. The project contains a public portfolio experience, client lead capture flow, and admin-managed content.

## What Was Updated Recently

1. Upgraded dependency baseline to current compatible versions with Django on LTS (`5.2.x`).
2. Tightened semantic safety by replacing wildcard imports and broad exception handling in authored code paths.
3. Completed strict code-quality cleanup on authored Python code (PEP 8 + Ruff rule set used in this repo).
4. Implemented centralized logging configuration with:
   - console handler
   - rotating file handler
   - environment-driven log level and log file name
5. Added structured logging calls in critical request flows (signup/login/contact/profile/detail paths).
6. Added GitHub Actions-based CI/CD automation with a quality gate workflow for feature and fix branches and an auto-deployment workflow for the `main` branch via AWS SSM.

## Tech Stack

- Python 3.12
- Django 5.2 LTS
- PostgreSQL (production) / SQLite (local fallback)
- Bootstrap + JavaScript + jQuery
- S3 storage support via `django-storages`

## Repository Layout

```text
portfolio_cum_blog/
├── blog/
├── portfolio/
├── portfolio_cum_blog/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── static/
├── templates/
├── manage.py
├── requirements.in
├── requirements.txt
└── README.md
```

## Prerequisites

1. Python 3.12+
2. `pip`
3. Virtual environment support (`venv`)

Optional:

1. PostgreSQL (if not using SQLite fallback)

## Local Setup

1. Clone and enter project

```bash
git clone https://github.com/gautamw3/portfolio_cum_blog.git
cd portfolio_cum_blog
```

2. Create and activate virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Create environment file (`.env`) and configure variables (example below)

```env
SECRET_KEY=replace-me
DEBUG=1
ALLOWED_HOSTS=127.0.0.1,localhost

ROOT_URLCONF=portfolio_cum_blog.urls

STATIC_URL=/static/
STATIC_ROOT=staticfiles
MEDIA_URL=/media/
MEDIA_ROOT=media

DATABASE_READY=0

LANGUAGE_CODE=en-us
TIME_ZONE=UTC
USE_I18N=1
USE_TZ=1

CRISPY_TEMPLATE_PACK=bootstrap4
DEFAULT_USER=1

EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_USE_TLS=0
EMAIL_HOST=
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_PORT=
APPLICATION_EMAIL=no-reply@example.com
DEFAULT_FROM_EMAIL=no-reply@example.com

LOG_LEVEL=INFO
LOG_FILE_NAME=application.log
```

5. Run migrations

```bash
python manage.py migrate
```

6. Start development server

```bash
python manage.py runserver
```

7. Open application

- http://127.0.0.1:8000/

## Logging

Centralized Django logging is configured in `portfolio_cum_blog/settings.py`.

Handlers:

1. Console handler for terminal logs
2. Rotating file handler writing to `logs/<LOG_FILE_NAME>`

Environment controls:

1. `LOG_LEVEL` (default: `INFO`)
2. `LOG_FILE_NAME` (default: `application.log`)

The application now logs key events for:

1. authentication (signup/login/logout)
2. profile and detail page rendering failures
3. contact/client lead workflows
4. input validation and endpoint misuse (invalid HTTP method / missing params)

## Quality and Verification Commands

Run strict lint rules used during hardening:

```bash
ruff check . --exclude portfolio/migrations,manage.py --select E,W,F,I,UP,B,SIM,PERF,RUF
```

Run formatting:

```bash
ruff format .
```

Run Django checks:

```bash
python manage.py check
```

Run tests:

```bash
pytest -q
```

## Git Hook Setup

This repository includes a pre-push hook that runs Black in check mode and the test suite before each push.

After cloning the repo, enable the hooks once from the repository root:

```bash
git config core.hooksPath .githooks
chmod +x .githooks/pre-push
```

These commands make Git use the repository-local hook directory for this clone. After that, every `git push` will stop if formatting or tests fail.

If you ever need to bypass the hook for a one-off push, use:

```bash
git push --no-verify
```

## CI/CD Setup and Current Workflow Guide

This repository currently uses two GitHub Actions workflows:

1. Quality Gate: [.github/workflows/quality-gate.yml](.github/workflows/quality-gate.yml)
   - Runs on pushes to `feature/*` and `fix/*` branches
   - Can also be run manually from the GitHub Actions tab
   - Validates dependencies, Django checks, tests, formatting, linting, security scans, and secret detection

2. Production Deployment: [.github/workflows/production-deployment.yml](.github/workflows/production-deployment.yml)
   - Runs automatically on pushes to `main`
   - Deploys the already-validated code to the EC2 instance through AWS Systems Manager
   - Does not run tests or linting itself; validation happens in the quality gate workflow first

### Required GitHub Configuration

Configure these repository secrets in GitHub before using the deployment workflow:

1. Repository Settings > Secrets and variables > Actions > Secrets
2. Add the required secrets:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_REGION`
   - `EC2_INSTANCE_ID`

### How to Pause or Stop Auto Deployments

The current implementation is push-based, so the simplest ways to pause deployment are:

1. Stop pushing to `main` until you are ready to deploy
2. Disable the workflow in GitHub Actions if you need to suspend it temporarily

### How to Trigger the Quality Checks Manually

1. Open the GitHub Actions tab
2. Select the “Quality Gate” workflow
3. Click “Run workflow”

This works whether auto deploy is enabled or disabled.

## Deployment Notes

1. In production (`DEBUG=0`), static/media storage uses the configured S3 backends.
2. Ensure AWS and database environment variables are provided before startup.
3. Keep `SECRET_KEY` private and use secure cookie/SSL settings in production.

## Contributing

1. Create a feature branch.
2. Keep authored code compliant with lint and tests.
3. Open a PR with a clear change summary.

## License

This project is licensed under the MIT License.
