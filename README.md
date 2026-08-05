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
7. Implemented customer review collection from frontend with admin approval workflow.
8. Implemented admin-native bulk SMS review invitations via AWS End User Messaging.
9. Added campaign-based invitation tracking with per-recipient submission status.
10. Added active-campaign dropdown based invitation mapping and normalized phone parsing.

## Tech Stack

- Python 3.12
- Django 5.2 LTS
- PostgreSQL (production) / SQLite (local fallback)
- Bootstrap + JavaScript + jQuery
- S3 storage support via `django-storages`

## Repository Layout

```text
PORTFOLIO-CUM-BLOG-PERSONAL/
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
git clone https://github.com/gautamw3/PORTFOLIO-CUM-BLOG-PERSONAL.git
cd PORTFOLIO-CUM-BLOG-PERSONAL
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

Centralized Django logging is configured in `portfolio_cum_blog
/settings.py`.

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

## Customer Reviews and SMS Invitations

The site now supports a complete review collection flow:

1. A public review form at `write-review/`
2. An admin-native bulk SMS sender at
   `Admin -> Portfolio -> Review Campaigns -> Send Review Invitation`
3. Admin review moderation (`is_approved`) before reviews are visible on frontend
4. Campaign-level invitation grouping and recipient-level tracking

### Admin Workflow

1. Create one or more review campaigns in `Review Campaigns`.
2. Mark campaigns as active (`is_active=True`) to make them selectable.
3. Open `Send Review Invitation` from Review Campaign list view.
4. Select one active campaign from dropdown.
5. Enter one or multiple recipients in one submit.
6. Submit to send SMS invitations and map recipients to the selected campaign.
7. Review tracking from campaign detail page (inline invitation rows).

### Recipient Input Format

Use one recipient per line in either format:

1. `Name, +1234567890`
2. `+1234567890`
3. `Name, 9876543210`

If local numbers are provided, the selected default country code is appended and
stored in normalized form.

On the send form, staff select an active campaign from a dropdown and send one or
many invitations in one action. Invitations are mapped to the selected campaign.

SMS invitations are sent through AWS End User Messaging SMS using the approved sender ID when configured.

### Message Templating

The SMS body supports placeholders:

1. `{name}` for recipient name
2. `{link}` for personalized review URL

If `{link}` is missing, the system appends the personalized review URL automatically.

### Review Visibility and Approval

1. Customer-submitted reviews are stored as not approved by default.
2. Only approved reviews are shown on homepage/about testimonial sections.
3. Approving from list view sets approval metadata.
4. Approving from detail page also sets `approved_by` and `approved_at`.
5. Unapproving clears approval metadata.

### Tracking Semantics

Invitation status values:

1. `pending`
2. `sent`
3. `failed`
4. `reviewed`

Campaign counters:

1. `sent_count`
2. `failed_count`
3. `submitted` (derived in admin from mapped invitations with submitted reviews)

Additional environment variables:

1. `AWS_REGION`
2. `AWS_EUM_ORIGINATION_IDENTITY`
3. `AWS_EUM_CONFIGURATION_SET_NAME`
4. `AWS_EUM_PROTECT_CONFIGURATION_ID`
5. `AWS_EUM_DEFAULT_MESSAGE_TYPE`
6. `REVIEW_INVITATION_DEFAULT_COUNTRY_CODE`

### Data Models Added/Updated

1. `ReviewCampaign` (with `is_active` support)
2. `ReviewInvitation` (tokenized recipient invitation + SMS tracking)
3. `Review` updated with moderation fields:
   - `is_approved`
   - `approved_by`
   - `approved_at`

### Notes

1. The invitation sending UX is intentionally centralized under `Review Campaigns`.
2. Recipient tracking is shown inline under each campaign detail page.
3. Public review submission is available through `write-review/`.

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
