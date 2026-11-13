.PHONY: install db-up db-down db-reset db-logs run

COMPOSE = docker compose --env-file .env -f docker-compose.yaml

# Specific dependencies needed can be found in the requirements.txt file
# Install all by running `make install`
install:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt

# Start the PostgreSQL database container
db-up:
	$(COMPOSE) up -d db

# Stop the PostgreSQL database container without deleting its data
db-down:
	$(COMPOSE) stop db

# Stop the PostgreSQL database container and delete its persistent data
db-reset:
	$(COMPOSE) stop db
	docker rm network-assessment-postgres
	docker volume rm network_assessment_postgres_data
	$(COMPOSE) up -d db

# View the logs of the database
db-logs:
	$(COMPOSE) logs -f db

# Run the management console Flask application
run:
	python3 api/app.py