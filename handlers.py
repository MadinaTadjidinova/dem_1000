import logging
import asyncio
import datetime
from aiogram import Bot, types, Router
from aiogram.filters import Command
from config import CHAT_ID, ADMIN_IDS, TOPICS, PAYMENT_REMINDER

router = Router()  # Используем Router

@router.message(Command("send"))
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
    await message.bot.send_message(CHAT_ID, text, message_thread_id=topic_id)
    await message.answer(f"✅ Сообщение отправлено в топик **{topic_name}**!")

async def auto_send_payment_reminder(bot: Bot):
    topic_id = TOPICS["общий"]
    while True:
        now = datetime.datetime.now()
        # if now.day == 1:  # Первое число месяца
        await bot.send_message(CHAT_ID, PAYMENT_REMINDER, message_thread_id=topic_id)
        logging.info(f"📨 Отправлено напоминание о платеже в общий чат.")
        await asyncio.sleep(300)  # Ждём 1 день
        # else:
        #     await asyncio.sleep(3600)  # Проверяем каждый час
