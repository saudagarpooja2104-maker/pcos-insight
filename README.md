# PCOS Insight

PCOS Insight is an educational screening-support and women's health monitoring prototype. It helps a signed-in user record cycle dates, symptoms, and lifestyle observations in one place. It does not diagnose PCOS or replace care from a qualified clinician.

## Implemented so far

The Django foundation includes sign-in, account registration with explicit health-data consent, cycle, symptom, and lifestyle entry forms, a private dashboard, consent withdrawal and restoration, a private profile and data overview, a monthly cycle calendar, personal cycle-interval and symptom-severity charts, descriptive record summaries, per-entry editing and deletion, password-confirmed account deletion, an educational PCOS learning page, and an authenticated date-range PDF export. The responsive frontend uses a shared stylesheet, navigation, and footer across the main pages. Dashboard, report, and chart data are limited to the signed-in user's records. The optional ultrasound prototype accepts private JPEG, PNG, or WebP images, validates and normalizes them, and provides a grayscale contrast preview; it does not classify or diagnose. Structured-data risk estimation remains deferred pending dataset and provenance review.

## Development setup

1. Install Python 3.11 or newer and MySQL 8.0 or newer.
2. Create and activate a virtual environment.
3. Install dependencies with `pip install -r requirements.txt`.
4. Copy `.env.example` to `.env` and set a fresh `DJANGO_SECRET_KEY` and database settings.
5. Create the configured MySQL database, then run `python manage.py migrate` and `python manage.py createsuperuser`.
6. Start the development server with `python manage.py runserver`.

For local development only, set `DB_ENGINE=sqlite` to use SQLite. Production deployments must set `DJANGO_DEBUG=False`, use HTTPS, configure allowed hosts, and provide a secure secret key.

## Public deployment preparation

The repository is prepared for a WSGI host with Gunicorn, PostgreSQL via `DATABASE_URL`, and WhiteNoise static-file serving. Before production startup, set `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, `DATABASE_URL`, and `PRIVATE_MEDIA_ROOT`. `PRIVATE_MEDIA_ROOT` must point to a persistent private volume; uploads must never be served as public static or media files. Run `python manage.py collectstatic --no-input` and `python manage.py migrate` as deployment steps, then run `python manage.py check --deploy` with the production environment configured.

This code is still a prototype. Do not enter real patient information or use it for clinical decisions. A public internet deployment also requires a hosting account, a connected Git repository, and review of the host's persistent storage and privacy controls. The current local SQLite database and upload folders are excluded from Git.

### Render demo

`render.yaml` describes a Render web service, managed PostgreSQL database, and a dedicated persistent volume for private uploads. It uses paid service, database, and storage plans so accounts and uploaded files can persist. Review the exact current estimate in Render before applying the Blueprint. As of the 2026-11-09 review, Render lists the small web plan at $7/month, the small PostgreSQL plan at $6/month, and persistent disks at $0.25/GB-month; database storage and bandwidth can add charges. The free PostgreSQL plan expires after 30 days and is not configured here. See [Render pricing](https://render.com/pricing) and [Render's disk policy](https://render.com/docs/disks).

To deploy this public demo, push the source to GitHub, connect the repository to Render, and create a new Blueprint Instance from `render.yaml`. The public repository contains source code only: do not commit `.env`, local SQLite databases, or media files. Review the generated service and database costs before applying. Do not deploy real patient information or use this prototype for clinical decisions.

Ultrasound image files are stored under `private_media/` and are served only through authenticated, owner-scoped views. Do not expose that directory through a web server, static-file mapping, or public media URL. Set upload-size limits at the reverse proxy or web server as well as in the form.

## Health data and safety

Health data is sensitive. The initial implementation requires authentication for health records, ties each record to its owner, and stores explicit consent status. Do not use real patient data or deploy this prototype for clinical use. Model outputs, when added, must be presented as estimates with limitations and must never be phrased as a diagnosis.

## Next milestones

1. Resolve dataset license and provenance questions recorded in `docs/dataset-assessment.md`.
2. Build the documented preprocessing and classifier-comparison pipeline only if the dataset meets the synopsis requirements.
3. Resolve the ultrasound dataset question before considering any learned classification or follicle detection.
4. Add project-specific recorded checks and resolve setup issues before demonstration.
