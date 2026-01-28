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
2. Create `.env` with required environment variables and secret file paths.
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
- `make remnawave-check`: validate Remnawave connectivity and endpoint mapping.

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
   - Sample: `{"create_user": "/api/users"}`.
5. Logs to inspect:
   - API/worker logs include structured JSON with `event=remnawave_endpoint_check` and `mode`.
   - Errors in strict mode prevent startup.

## Manual QA (acceptance)
- **S1**: `/start` shows home screen with buttons; `/start ref_CODE` assigns referrer and shows Home.
- **S2**: Buy → Пробный период 24ч works once; second attempt shows "trial already used".
- **S3**: Buy → выбрать тариф → выбрать локацию → оплатить Stars sends invoice; successful payment triggers provisioning job.
- **S4**: Buy another period for same plan/location extends expiration (check in DB).
- **S5**: After a referred user pays, referrer earns 20% once per payment.
- **S6**: Support → создать обращение creates ticket; Support → мои обращения → ответить appends messages; Admin can reply.
- **S7**: Reconcile generates only one notice for 3d/1d/expired per subscription.
- **S8**: Duplicate Remnawave webhooks enqueue idempotent jobs only once.
- **S9**: Admin → sync servers/users enqueues jobs and logs counts.
- **S10**: Worker retries failed jobs with backoff and marks failures after max attempts.
