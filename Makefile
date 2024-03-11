start:
	docker-compose up -d
	@sleep 5  # Espera breve para asegurarse de que la base de datos esté lista
	docker-compose exec -T db psql -U admin -d users -c "CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, user_id INTEGER UNIQUE, acciones TEXT[]);"
	# docker-compose exec bot python telegram.py

stop:
	docker-compose down

restart: stop start

.PHONY: start stop restart
