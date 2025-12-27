#!/usr/bin/env bash
# Выходим при ошибке
set -o errexit

# 1. Устанавливаем библиотеки
pip install -r requirements.txt

# 2. Собираем статику (CSS, картинки)
python manage.py collectstatic --no-input

# 3. Применяем миграции (создаем таблицы в базе)
python manage.py migrate
python manage.py createsuperuser --noinput || true