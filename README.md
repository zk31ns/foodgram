[![Foodgram workflow]

#  Проект Foodgram

## Описание проекта
Данный проект представляет собой социальную сеть, которая позволяет пользователям публиковать свои кулинарные рецепты, подписываться на других авторов, добавлять рецепты в избранное и формировать список покупок на основе выбранных блюд. На сайте необходимо создать аккаунт для добавления рецептов блюд, подписки на других пользователей. Рецепты можно добавить в избраное или в список покупок. Также можно скачать список покупок, где будут перечислены ингредиенты.

## Использованные технологии

- Python — разработка backend
- Django — веб-фреймворк
- Django REST Framework — создание API
- Nginx — веб-сервер и прокси
- Docker — контейнеризация и деплой
- PostgreSQL — база данных
- npm — управление пакетами frontend
- React — фреймворк для frontend
- GitHub Actions — автоматизация CI/CD


## Запуск проекта локально

### 1. Склонировать на компьютер репозиторий

### 2. Заполнить переменные окружения
Для работы проекта необходимо создать файл .env и заполнить переменные окружения добавив следующие значения:
```env
DB_NAME=your_db_name
DATABASE_TYPE=postgresql
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
DB_HOST=db
DB_PORT=5432
SECRET_KEY=your_django_secret_key
DEBUG=True
ALLOWED_HOSTS=your_domain.com,localhost,127.0.0.1
```
### 3. Создайте и активируйсте виртуальное окружение
```bash
python -m venv venv
source venv/Scripts/activate
```
### 4. Выполните миграции установив зависимости для backend
```bash
pip install -r requirements.txt
python manage.py migrate
```
### 5. Запустите frontend и backend проект
```bash
npm start
python manage.py runserver
```
### 6. В браузере зайдите по адресу http://localhost:8000

## Запуск проекта локально в Docker

### 1. Запустите Docker Compose
```bash
docker-compose up -d --build
```
### 2. Выполните миграции, соберите статику и импортируйте ингредиенты
```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py collectstatic
docker compose exec backend python manage.py load
```
### 3. Создайте суперпользователя для доступа к панели администрирования
```bash
docker-compose exec backend python manage.py createsuperuser
```
### 4. Откройте браузер и перейдите по адресу http://localhost:8000/
Для доступа к панели администрирования зайдите по адресу http://localhost:8000/admin
Добавьте нужные вам теги, например "Завтрак", "Обед", "Ужин".

### Сайт проекта
https://fudo.ddns.net
