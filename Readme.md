# shcut

URL-шейкер с аналитикой и geo-блокировкой.

Демо: [shcut.onrender.com](https://shcut.onrender.com)

---

## API Endpoints

**Auth**
- POST /api/signup — регистрация
- POST /api/login — вход
- POST /api/logout — выход

**URLs**
- GET /api/urls — список ссылок (макс 5)
- POST /api/shorten — создать короткую ссылку
- DELETE /api/url/<code> — удалить ссылку
- GET /api/url/<code>/clicks — кол-во кликов

**Статистика**
- GET /api/url/<code>/stats — полная статистика
- GET /api/url/<code>/settings — настройки
- PUT /api/url/<code>/settings — обновить настройки

**Редирект**
- GET /<code> — переход на оригинальный URL

---

## Быстрый старт

    git clone https://github.com/твой-username/shcut.git
    cd shcut/backend
    pip install -r requirements.txt

Создай .env:

    DB_HOST=хост_бд
    DB_USER=пользователь
    DB_PASSWORD=пароль
    DB_NAME=postgres
    SECRET_KEY=секрет

Запуск:

    python migrate.py
    python app.py

---

## Деплой на Render

Build: cd backend && pip install -r requirements.txt

Start: cd backend && gunicorn app:app

Env:

    DB_HOST=aws-1-eu-west-1.pooler.supabase.com
    DB_PORT=6543
    DB_USER=postgres.amihdahmqdkvksfzdico
    DB_PASSWORD=пароль
    DB_NAME=postgres
    SECRET_KEY=секрет
    SESSION_COOKIE_SECURE=True
    MAX_URLS_PER_USER=5

---

## Технологии

Python + Flask, PostgreSQL, HTML/CSS/JS + Chart.js, Render

---