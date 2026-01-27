# Horizon VPN Platform

Horizon VPN is a Telegram-first subscription platform with a FastAPI backend, aiogram v3 bot, and a background worker responsible for all external side effects. The system integrates with Remnawave for provisioning, supports Telegram Stars payments, provides admin tooling, and enforces idempotent workflows.

## Architecture
- **Bot**: aiogram v3, single editable root message per user, callback-driven navigation.
- **API**: FastAPI service for health checks, webhooks, and optional cabinet features.
- **Worker**: async processor for provisioning, Remnawave sync, notifications, and retries.
- **Data**: Postgres (async SQLAlchemy + Alembic) and Redis (locks, rate limits, jobs).

## Quickstart
1. Create secret files (tokens are never stored in the repo):
   - `secrets/bot_token`
   - `secrets/remnawave_token`
   - `secrets/remnawave_webhook_secret`
   - `secrets/cabinet_jwt_secret`
2. Copy env file:
   ```bash
   cp .env.example .env
   ```
3. Start services:
   ```bash
   make up
   ```
4. Run migrations and seed:
   ```bash
   make migrate
   make seed
   ```
5. Verify health:
   ```bash
   curl http://localhost:8000/health
   ```

## Runbook
- `make up`: start Postgres, Redis, API, bot, worker.
- `make down`: stop all services.
- `make logs`: tail compose logs.
- `make migrate`: run Alembic migrations.
- `make seed`: seed plans, locations, content.
- `make restart`: restart all services.

## How to validate Remnawave endpoints
1. Open the Remnawave panel and view the Swagger docs:
   - Log in to the Remnawave panel.
   - Open the API docs (usually `/swagger` or `/docs`).
2. Test connectivity with the provided script in the API container:
   ```bash
   docker compose exec api python -m app.integrations.remnawave.check
   ```
   This command uses `REMNAWAVE_BASE_URL` and the token file. The token is never printed.
3. Strict vs compat mode:
   - `REMNAWAVE_API_MODE=strict` fails fast on missing/invalid endpoints.
   - `REMNAWAVE_API_MODE=compat` allows overrides via `REMNAWAVE_ENDPOINT_OVERRIDES_JSON`.
4. To override endpoints safely:
   - Provide a JSON map of endpoint names to paths.
   - Example: `{"create_user": "/api/users"}`.
5. Logs to inspect:
   - API/worker logs include structured JSON with `event=remnawave_endpoint_check` and `mode`.
   - Errors in strict mode prevent startup.

## Manual QA (acceptance)
- **S1**: `/start` and `/start ref_CODE` should create a user and handle referrals.
- **S2**: trial can be used only once.
- **S3**: buy flow creates intent, issues invoice, and triggers provisioning.
- **S4**: renew subscription extends expiration.
- **S5**: referral credited once per payment.
- **S6**: support tickets allow user/admin messages.
- **S7**: notifications for 3d/1d/expired only once.
- **S8**: duplicate webhooks are idempotent.
- **S9**: sync servers/users via admin.
- **S10**: provisioning failures are retried by worker.
