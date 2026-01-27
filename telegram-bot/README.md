# Horizon VPN — Telegram Bot (LONG POLLING) + Telegram Stars + Remnawave

Стек:
- Python 3.12
- aiogram v3
- PostgreSQL + SQLAlchemy 2 + Alembic
- Redis (FSM + click locks + Streams queue)
- httpx (Remnawave API)
- Docker Compose
- Notifications worker (подписка истекает)

## Важные принципы
- Single-message UI: главное меню редактируется (editMessageText), чат не заспамливается.
- Secrets: только `/opt/horizon/secrets/*` (не печатать в чат).
- Оплата: Telegram Stars (currency `XTR`, provider_token пустой).
- Идемпотентность: каждый платеж имеет `idempotency_key`, повторно не зачисляется.
- Защита от двойного клика: Redis lock 3 секунды.
- Возвраты Stars: обработка `refunded_payment` помечает платёж как `refunded` и обновляет экран статуса.

## Пути на HUB
Проект:
`/opt/horizon/stacks/telegram-bot/`

Секреты:
`/opt/horizon/secrets/`

## Подготовка секретов (вводишь значения сам)
Файлы:
- `/opt/horizon/secrets/telegram-bot_token`
- `/opt/horizon/secrets/telegram-bot_db_password`
- `/opt/horizon/secrets/telegram-bot_redis_password`
- `/opt/horizon/secrets/remnawave_api_token`

Права:
`chmod 600` на все файлы секретов.

## Запуск (Termius)
```bash
cd /opt/horizon/stacks/telegram-bot
sudo docker compose config
sudo docker compose build
sudo docker compose up -d
sudo docker compose logs -f bot
```

## Миграции БД (обязательно при релизе)
```bash
cd /opt/horizon/stacks/telegram-bot
sudo docker compose exec bot alembic upgrade head
```

## STOP HERE — контрольные точки
1) Проверка контейнеров:
```bash
sudo docker compose ps
```
Ожидается: `bot`, `broadcast-worker`, `retry-worker`, `notifications-worker`, `bot-db`, `bot-redis` в статусе `running (healthy)`.

2) Проверка healthcheck внутри контейнера:
```bash
sudo docker compose exec bot python -m hzn_bot.healthcheck
```
Ожидается: команда завершается без ошибок (exit code 0).

3) Проверка миграций:
```bash
sudo docker compose exec bot alembic current
```
Ожидается: `0003_sales_ready` в актуальной версии.

## Перезапуск и обновление
```bash
cd /opt/horizon/stacks/telegram-bot
sudo docker compose pull
sudo docker compose up -d --build
sudo docker compose exec bot alembic upgrade head
```

## Переменные окружения (важное)
- `ADMIN_IDS` — обязательный allowlist админов (пример: `1375385135`).
- `INVOICE_TTL_SECONDS` — TTL счёта в секундах (по умолчанию 3600).
- `REDIS_PROVISION_LOCK_SECONDS` — блокировка на время выдачи доступа (по умолчанию 30).
- `REMNAWAVE_RETRY_ATTEMPTS` / `REMNAWAVE_RETRY_MIN_SECONDS` / `REMNAWAVE_RETRY_MAX_SECONDS` — повторные попытки Remnawave.
- `TRIAL_DAYS` — длительность триала в днях (по умолчанию 1).
- `SUPPORT_RATE_LIMIT_SECONDS` — анти-спам задержка для тикетов (по умолчанию 120).
- `NOTIFICATIONS_INTERVAL_SECONDS` / `NOTIFICATIONS_BATCH_LIMIT` — частота и пачка уведомлений.

## Безопасность
- Секреты только через `/opt/horizon/secrets/*`.
- Не логировать токены/пароли и не отправлять их в чат.

## Команды и callback_data
Команды:
- `/start` — инициализация пользователя + показ главного экрана.

Callback-экранные маршруты (основные):
- `m:main` — главное меню.
- `m:status` — личный кабинет.
- `m:buy` — выбор тарифа.
- `m:instr` — инструкция подключения.
- `m:support` — поддержка.

Callback покупки:
- `b:plan:classic`, `b:plan:premium` — выбор тарифа.
- `b:period:<plan>:30|90|180` — выбор периода.
- `b:loc:<plan>:<days>:<location>` — выбор локации.
- `b:promo` — ввод промокода.
- `b:check:<idem>` — проверка оплаты.
- `b:cancel:<idem>` — отмена счёта.
- `b:trial` — запуск триала.

Админ:
- `a:home` — главная админка.
- `a:dash` — дашборд.
- `a:payouts:<offset>` — список заявок.
- `a:payout_ok:<id>` — подтвердить выплату.
- `a:payout_no:<id>` — отклонить выплату.
- `a:test_credit:1000` — тестовое начисление.
- `a:test_payout:600` — тестовая заявка.
- `a:test_buy:classic:30`, `a:test_buy:premium:30` — тестовая покупка.
- `a:manual:0` — ручные платежи.
- `a:promo:0` — промокоды.

## Матрица тестов (ручная проверка)
1) `/start` → главное меню.
2) `m:buy` → выбор тарифа.
3) `b:plan:classic` → выбор периода.
4) `b:period:classic:30` → подтверждение оплаты + ссылка Stars.
5) `b:check:<idem>` → подтверждение статуса (paid/fulfilled/expired).
6) `b:cancel:<idem>` → отмена счёта.
7) `m:status` → активная подписка и дата окончания.
8) `m:ref` → реферальная ссылка.
9) `m:payouts` → баланс доступен/ожидает.
10) `m:support` → экран поддержки.
11) `a:home` (админ) → панель администратора.
12) `a:dash` (админ) → дашборд.
13) `a:payouts:0` (админ) → список заявок.
14) `a:payout_ok:<id>` / `a:payout_no:<id>` → обработка заявок.
