.PHONY: up down logs test migrate seed dev

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f web

test:
	pytest

migrate:
	alembic upgrade head

seed:
	python -m scripts.seed_demo

dev:
	uvicorn app.main:app --reload
