from aiogram import Bot

# 🔹 Бот для пользователей
SPONSOR_BOT_TOKEN = "7610424500:AAG9guwRESV6ACNSDhUohUi3X5LSKFBCKJE"
sponsor_bot = Bot(token=SPONSOR_BOT_TOKEN)

# 🔹 Бот для админов
ADMIN_BOT_TOKEN = "7847845721:AAGFDHoGFpJOrI6zx1kteR204EWER9sONjc"
admin_bot = Bot(token=ADMIN_BOT_TOKEN)

# 🔹 Основные ID
CHAT_ID = "-1002267046905"  # Группа для спонсоров
ADMIN_CHAT_ID = "-1002446687533"  # Группа для админов
ADMIN_IDS = [6946609744, 1138708088]  

TOPICS = {
    "онас": 24,
    "отчёт": 18,
    "джентельмен": 37,
    "правила": 39,
    "реквизит": 20,
    "general": 1,
    "проверка": 269
}

PAYMENT_REMINDER = (
    "🔔 Напоминание: Приближается новый месяц, не забудьте внести 1000 сом на поддержку библиотеки! 💰\n"
    "📌 Реквизиты можно найти в топике 'Реквизиты'.\n"
    "Спасибо за вашу поддержку! ❤️"
)