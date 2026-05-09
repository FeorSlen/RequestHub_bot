# Anonymous Petition Bot

Telegram-бот для анонимных обращений. Пользователь отправляет текст, получает UUID и может проверить статус ответа по нему. Администратор видит очередь, может ответить или пометить как спам.

Персональные данные не хранятся. Анонимность на уровне приложения — Telegram и сервер остаются точками доверия.

## Стек

- Python 3.11+ / aiogram 3
- SQLite (WAL) + aiosqlite
- FSM, rate limiting middleware

## Установка

```bash
git clone https://github.com/FeorSlen/RequestHub_bot.git
cd RequestHub_bot
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Конфигурация

Создай `.env`:

```
API_TOKEN=<telegram bot token>
ADMIN_TG_IDS=123456789,987654321
DATABASE_PATH=data/db.sqlite3
```

## Запуск

```bash
python main.py
```

## Структура

```
src/
├── user/        # хендлеры и логика пользователя
├── admin/       # панель администратора
├── middleware/  # rate limiting, инъекция БД
├── utils/       # фильтры, базовое меню
└── db_connector.py
```
