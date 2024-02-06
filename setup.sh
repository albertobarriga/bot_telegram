#!/bin/bash

# Crear un entorno virtual
python3 -m venv .venv

# Activar el entorno virtual
source .venv/bin/activate

# Instalar los requisitos desde el archivo requirements.txt
pip install -r requirements.txt

# Ejecutar el script telegram.py
python3 telegram.py
