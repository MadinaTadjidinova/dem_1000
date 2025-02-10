import logging
import asyncio
import datetime
from aiogram import Bot, types, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.filters import Command
from config import CHAT_ID, ADMIN_IDS, TOPICS, PAYMENT_REMINDER, sponsor_bot
from google_sheets import sheet

router = Router()  # Используем Router

# ✅ Настраиваем логирование
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 🔹 Функция для создания кнопок "О нас"
def get_about_us_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎥 Видео", callback_data="about_video")],
            [InlineKeyboardButton(text="🖼 Фото", callback_data="about_photo")],
            [InlineKeyboardButton(text="📂 Проекты", callback_data="about_projects")],
            [InlineKeyboardButton(text="📜 История", callback_data="about_history")]
        ]
    )

async def send_about_menu(bot: Bot):
    """Отправляет меню в топик 'О нас' при запуске."""
    topic_id = TOPICS["онас"]
    await bot.send_message(
        CHAT_ID,
        "📢 Добро пожаловать в раздел 'О нас'!\nВыберите интересующий раздел:",
        reply_markup=get_about_us_keyboard(),
        message_thread_id=topic_id
    )
    logging.info("📌 Меню 'О нас' отправлено автоматически.")

@router.message()
async def auto_about_menu(message: Message):
    """Автоматически показывает меню, если кто-то пишет в топик 'О нас'."""
    topic_id = TOPICS["онас"]
    
    if message.message_thread_id == topic_id:
        logging.info(f"📌 В топике 'О нас' появилось новое сообщение от {message.from_user.username}. Отправляем меню.")
        await message.answer("📢 Выберите раздел:", reply_markup=get_about_us_keyboard())

# 🔹 Обработчики кнопок с `edit_message_text`
@router.callback_query(lambda c: c.data.startswith("about_"))
async def about_callback_handler(callback: types.CallbackQuery):
    """Редактирует сообщение с кнопками только для пользователя, который нажал"""
    responses = {
        "about_video": "🎥 **Видео о нашем проекте**\n[Ссылка на видео](https://example.com)",
        "about_photo": "🖼 **Фото о нашем проекте**\n[Галерея фото](https://example.com)",
        "about_projects": "📂 **Наши проекты**:\n1️⃣ Проект 1 - описание\n2️⃣ Проект 2 - описание\n3️⃣ Проект 3 - описание",
        "about_history": "📜 **История проекта**:\nНаш проект был создан в ... (тут можно добавить описание)."
    }

    text = responses.get(callback.data, "Ошибка, попробуйте снова.")

    # Редактируем только сообщение пользователя
    await callback.message.edit_text(
        text=text,
        reply_markup=get_about_us_keyboard()  # Оставляем кнопки, чтобы можно было выбрать снова
    )
    await callback.answer()


# ✅ Обработчик команды /send
@router.message(Command("send"))
async def send_to_topic(message: types.Message):
    """Отправка сообщений администраторами в топики"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет прав на отправку сообщений.")
        return

    # Определяем текст сообщения: берем caption, если есть фото/видео, иначе берем message.text
    raw_text = message.caption if message.caption else message.text

    if not raw_text:
        await message.answer("❌ Укажите текст сообщения после команды `/send`.")  
        return

    args = raw_text.split(maxsplit=2)

    if len(args) < 3:
        await message.answer("❌ Используйте формат: `/send [топик] [текст]`")  
        return

    topic_name = args[1].lower()
    text = args[2]

    if topic_name not in TOPICS:
        await message.answer(f"❌ Такого топика нет. Доступные: {', '.join(TOPICS.keys())}")
        return

    topic_id = TOPICS[topic_name]

    # 🖼 Фото
    if message.photo:
        photo = message.photo[-1].file_id
        await message.bot.send_photo(CHAT_ID, photo=photo, caption=text, message_thread_id=topic_id)

    # 🎥 Видео
    elif message.video:
        video = message.video.file_id
        await message.bot.send_video(CHAT_ID, video=video, caption=text, message_thread_id=topic_id)

    # 📁 Документ (PDF, файлы)
    elif message.document:
        document = message.document.file_id
        await message.bot.send_document(CHAT_ID, document=document, caption=text, message_thread_id=topic_id)

    # 🎙 Голосовое сообщение
    elif message.voice:
        voice = message.voice.file_id
        await message.bot.send_voice(CHAT_ID, voice=voice, caption=text, message_thread_id=topic_id)

    # 📝 Обычное текстовое сообщение
    else:
        await message.bot.send_message(CHAT_ID, text, message_thread_id=topic_id)

    await message.answer(f"✅ Сообщение отправлено в топик **{topic_name}**!")


async def auto_send_payment_reminder(bot: Bot):
    """Авто-напоминание о платеже"""
    topic_id = TOPICS["общий"]
    while True:
        now = datetime.datetime.now()
        await bot.send_message(CHAT_ID, PAYMENT_REMINDER, message_thread_id=topic_id)
        logging.info(f"📨 Отправлено напоминание о платеже в общий чат.")
        await asyncio.sleep(86400)  # Ждём 1 день (86400 секунд)


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
