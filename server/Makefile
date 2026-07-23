.PHONY: dev migrate seed explorer

dev:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

migrate:
	alembic upgrade head

seed:
	python -m data.seed

explorer:
	python -m data.explorer
