import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import logging
import datetime

TOKEN = "7847845721:AAGFDHoGFpJOrI6zx1kteR204EWER9sONjc"
CHAT_ID = "-1002267046905" 
ADMIN_IDS = [6946609744] 

TOPICS = {
    "онас" : 24,
    "общий": 2,  
    # "цитаты": 234567,  
    "финансовый": 14,
    "отчёт": 18,
    "вопросы": 5,
    "feedback": 16,
    "QA": 5,
    "джентельмен": 37,
    "правила": 39,
    "реквизит": 18,
    "general": 1
}

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Напоминание о платеже
PAYMENT_REMINDER = (
    "🔔 Напоминание: Приближается новый месяц, не забудьте внести 1000 сом на поддержку библиотеки! 💰\n"
    "📌 Реквизиты можно найти в топике 'Реквизиты'.\n"
    "Спасибо за вашу поддержку! ❤️"
)

# Команда для отправки сообщений вручную
@dp.message(Command("send"))
async def send_to_topic(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет прав на отправку сообщений.")
        return
    
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer("❌ Используйте формат: `/send [топик] [текст]`")
        return
    
    topic_name = args[1].lower()
    text = args[2]

    if topic_name not in TOPICS:
        await message.answer(f"❌ Такого топика нет. Доступные: {', '.join(TOPICS.keys())}")
        return
    
    topic_id = TOPICS[topic_name]
    
    await bot.send_message(CHAT_ID, text, message_thread_id=topic_id)
    await message.answer(f"✅ Сообщение отправлено в топик **{topic_name}**!")



# async def auto_send_payment_reminder():
#     topic_general = TOPICS["общий"]  
#     # topic_financial = TOPICS["финансовый"]  
    
#     while True:
#         now = datetime.datetime.now()
#         last_day = (now.replace(day=28) + datetime.timedelta(days=4)).replace(day=1) - datetime.timedelta(days=1)  # Последний день месяца

#         if now.day == last_day.day:  # Проверяем, сегодня ли последний день месяца
#             # Отправляем напоминание в "Общий чат"
#             await bot.send_message(CHAT_ID, PAYMENT_REMINDER, message_thread_id=topic_general)
#             logging.info("📨 Отправлено напоминание о платеже в 'Общий чат'.")
            
#             # Отправляем напоминание в "Финансовый отчет"
#             # await bot.send_message(CHAT_ID, PAYMENT_REMINDER, message_thread_id=topic_financial)
#             # logging.info("📨 Отправлено напоминание о платеже в 'Финансовый отчет'.")

#             # Ждем до следующего дня, чтобы не спамить
#             await asyncio.sleep(86400)  # 24 часа (1 день)
#         else:
#             # Ждём до следующего дня, если сегодня не последний день месяца
#             await asyncio.sleep(3600)  # Проверяем каждый час



# Функция для автоматической отправки напоминания о платеже раз в 1 минуту
async def auto_send_payment_reminder():
    topic_id = TOPICS["общий"]  # ID топика "Общий чат"
    # topic_financial = TOPICS["финансовый"]
    while True:
        await bot.send_message(CHAT_ID, PAYMENT_REMINDER, message_thread_id=topic_id)
        logging.info(f"📨 Отправлено напоминание о платеже в общий чат.")

         # Отправляем напоминание в "Финансовый отчет"
        # await bot.send_message(CHAT_ID, PAYMENT_REMINDER, message_thread_id=topic_financial)
        # logging.info("📨 Отправлено напоминание о платеже в 'Финансовый отчет'.")

        await asyncio.sleep(60)  # Ждём 1 минуту перед следующим напоминанием


async def main():
    logging.basicConfig(level=logging.INFO)
    asyncio.create_task(auto_send_payment_reminder())  # Запускаем авто-напоминание о платеже
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())