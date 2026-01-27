.PHONY: up down logs migrate seed restart

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

migrate:
	docker compose exec api alembic upgrade head

seed:
	docker compose exec api python -m app.db.seed

restart:
	docker compose restart
