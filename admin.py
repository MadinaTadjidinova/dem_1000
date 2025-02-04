import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import logging

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

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())