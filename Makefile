.PHONY: install lint format typecheck test run deploy-dev deploy-prod remove-dev remove-prod info-dev info-prod

install:
	python -m pip install --upgrade pip
	pip install -r requirements-dev.txt
	npm install

lint:
	ruff check .

format:
	black .

typecheck:
	mypy src

test:
	pytest -q

run:
	uvicorn src.app.main:app --reload

deploy-dev:
	npm run deploy:dev

deploy-prod:
	npm run deploy:prod

remove-dev:
	npm run remove:dev

remove-prod:
	npm run remove:prod

info-dev:
	npm run info:dev

info-prod:
	npm run info:prod
