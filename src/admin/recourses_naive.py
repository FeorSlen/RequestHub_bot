#TODO: вынести это все в ресурсные файлы для редактирования в админке и локализации из коробки

# src/admin/resources.py

ADMIN_MENU_TEXT = "🛠 Меню админ-панели"
ADMIN_ACTIONS_TEXT = "📋 Доступные действия для обращения"

UNPROCESSED_COUNT = lambda count: f"📬 Количество необработанных запросов: {count}"
NO_UNPROCESSED = "✅ Все обращения обработаны! Новых запросов нет."

REQUEST_DISPLAY = lambda req_id, text: (
    f"📩 Обращение\n"
    f"🆔 ID: `{req_id}`\n\n"
    f"Текст обращения\n"
    f"📝 {text}\n"
)

MARKED_AS_SPAM = "🚫 Обращение помечено как спам. Загружаю следующее..."
WRITE_ANSWER_PROMPT = "✍️ Напишите ответ на обращение:"
ANSWER_SAVED = "💾 Ответ сохранён! Загружаю следующее..."

NO_REQUEST_SELECTED = "⚠️ Нет выбранного обращения. Начните с просмотра запросов."