.PHONY: install dev test clean migrate

# Install dependencies
install:
	pip install -r requirements.txt

# Run development server
dev:
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run tests
test:
	pytest tests/ -v --cov=. --cov-report=html

# Clean cache and temporary files
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -name "*.pyc" -delete
	rm -rf .pytest_cache/
	rm -rf htmlcov/

# Database migrations
migrate:
	alembic upgrade head

# Create new migration
migration:
	alembic revision --autogenerate -m "$(name)"

# Format code
format:
	black .
	
# Lint code
lint:
	flake8 .
	mypy .

# Run with Docker
docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

# Setup development environment
setup: install
	pre-commit install
	echo "Development environment ready!"
