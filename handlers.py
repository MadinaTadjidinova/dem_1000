import logging
import asyncio
import datetime
from aiogram import Bot, types, Router
from aiogram.filters import Command
from config import CHAT_ID, ADMIN_IDS, TOPICS, PAYMENT_REMINDER, sponsor_bot
from google_sheets import sheet

router = Router()  # Используем Router

# ✅ Настраиваем логирование
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

@router.message(Command("send"))
async def send_to_topic(message: types.Message):
    """Отправка сообщений администраторами в топики"""
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
    """Авто-напоминание о платеже"""
    topic_id = TOPICS["общий"]
    while True:
        now = datetime.datetime.now()
        await bot.send_message(CHAT_ID, PAYMENT_REMINDER, message_thread_id=topic_id)
        logging.info(f"📨 Отправлено напоминание о платеже в общий чат.")
        await asyncio.sleep(60)  # Ждём 1 день (86400 секунд)

# 🆕 Новый обработчик кнопок подтверждения/отклонения платежей
@router.callback_query()
async def process_payment_action(callback: types.CallbackQuery):
    """Обрабатывает кнопки 'Подтвердить' и 'Отклонить'"""
    data = callback.data.split("|")

    if len(data) < 3:
        await callback.answer("❌ Ошибка данных!", show_alert=True)
        return

    action, user_id, amount = data[0], data[1], data[2]
    logging.info(f"🟢 Получен callback: {action}, user_id={user_id}, amount={amount}")

    # 🔹 Ищем платеж в Google Sheets
    records = [{k.strip(): v for k, v in row.items()} for row in sheet.get_all_records()]  # Убираем лишние пробелы
    row_number = None

    for i, row in enumerate(records, start=2):  # Первая строка — заголовки
        logging.info(f"🔍 Проверяем строку {i}: {row}")
        if str(row["Telegram ID"]) == str(user_id) and str(row["Сумма"]) == str(amount):
            row_number = i
            break

    if row_number is None:
        logging.warning(f"❌ Платеж не найден! user_id={user_id}, amount={amount}")
        await callback.answer("❌ Платеж не найден в Google Sheets!", show_alert=True)
        return

    if action == "confirm":
        sheet.update_cell(row_number, 6, "✅ Подтвержден")
        await callback.message.edit_caption(
            f"✅ Чек от @{callback.from_user.username} подтвержден!",
            reply_markup=None
        )
        await sponsor_bot.send_message(user_id, "✅ Ваш платеж подтвержден!")
        logging.info(f"✅ Чек от user_id={user_id} на сумму {amount} сом подтвержден!")

    elif action == "reject":
        sheet.update_cell(row_number, 6, "❌ Отклонен")
        await callback.message.edit_caption(
            f"❌ Чек от @{callback.from_user.username} отклонен!",
            reply_markup=None
        )
        await sponsor_bot.send_message(user_id, "❌ Ваш платеж отклонен. Попробуйте отправить другой чек.")
        logging.info(f"❌ Чек от user_id={user_id} на сумму {amount} сом отклонен!")

    await callback.answer()
