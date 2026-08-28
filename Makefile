.PHONY: install test run compose-up compose-down lint

install:
	python -m pip install -e '.[test]'

test:
	pytest -q

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

compose-up:
	docker compose up --build -d

compose-down:
	docker compose down

lint:
	python -m compileall app tests
