#!/usr/bin/env bash
# Salir si hay un error
set -o errexit

pip install -r requirements.txt

# Ejecutar las migraciones de Flask-Migrate
flask db upgrade