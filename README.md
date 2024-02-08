- HACER ENTORNO VIRTUAL:
python3 -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt



-ACCEDER A LA BASE DE DATOS:

psql -U admin -d users

SELECT * FROM users;



-CREAR TABLA EN LA BASE DE DATOS:

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE,
	acciones text[]
);

ALTER TABLE users
ADD COLUMN acciones text[];