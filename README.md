📨 Anonymous Requests Bot

Бот для анонимной отправки обращений с возможностью отслеживания их статуса по уникальному идентификатору.
Бот не требует регистрации и не хранит персональные данные пользователей.

Каждому обращению присваивается уникальный идентификатор (UUID), который используется для получения ответа.

⚠️ Анонимность сохраняется при условии:
отсутствия компрометации устройства пользователя
отсутствия компрометации инфраструктуры Telegram
корректной эксплуатации сервиса

🛠 Технологии

- Python 3.12
- aiogram 3
- SQLite
- FSM (Finite State Machine)
- кастомные middleware (rate limiting, DI для БД)

📦 Установка

git clone https://github.com/your-repo/anon-bot.git \
cd anon-bot \
python -m venv venv \
source venv/bin/activate \
pip install -r requirements.txt


⚙️ Настройка

Создай .env файл:

API_TOKEN=your_telegram_bot_token \
ADMIN_TG_IDS=123456789,987654321 \
ADMIN_SECRET=your_secret_key \


▶️ Запуск
python main.py


🧩 Архитектура\
src/\
├── user/          # пользовательские хендлеры\
├── admin/         # админ-панель\
├── middleware/    # rate limit, db DI\
├── utils/         # меню, фильтры, утилиты\
├── db_connector   # асинхронная обёртка над SQLite