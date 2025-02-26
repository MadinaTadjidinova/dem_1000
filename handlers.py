import logging
import asyncio
import datetime
import time
import os
from aiogram import Bot, types, Router
from aiogram.filters import Command
from config import CHAT_ID, ADMIN_IDS, TOPICS, PAYMENT_REMINDER, sponsor_bot
from google_sheets import sheet, update_payment_status
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, FSInputFile, InputMediaPhoto, InputMediaVideo, InputMediaDocument
from config import CHAT_ID, TOPICS

router = Router()  # Используем Router

FAQ_TOPIC_ID = TOPICS["правила"] 
REPORT_TOPIC_ID = TOPICS.get("отчёт")

# ✅ Настраиваем логирование
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

# 🔹 Директория для отчетов
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)  # Создаем папку, если ее нет

# 🔹 Словарь для хранения путей к последним отчетам
REPORT_FILES = {
    "events": None,
    "finance": None
}
# Храним ID ОДНОГО сообщения с отчетами
REPORT_FILES = None

# 🔹 ID топика для отчетов
REPORT_TOPIC_ID = TOPICS.get("отчёт", None)



# Кнопки выбора отчетов
def get_reports_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Отчет мероприятий", callback_data="show_events_report")],
            [InlineKeyboardButton(text="💰 Финансовый отчет", callback_data="show_finance_report")]
        ]
    )

# 📥 **Обработчик загрузки отчета (только обновление сообщения)**
@router.message(lambda message: message.document and message.caption and message.caption.startswith("/upload_report"))
async def handle_report_upload(message: types.Message, bot: Bot):
    global REPORT_FILES

    args = message.caption.split()
    if len(args) < 2 or args[1] not in ["events", "finance"]:
        await message.answer("❌ Используйте команду: `/upload_report events` или `/upload_report finance`.")
        return

    report_type = args[1]
    file_path = os.path.join(REPORTS_DIR, f"{report_type}.pdf")

    # 📥 Сохраняем файл
    await bot.download(file=message.document, destination=file_path)

    # 🔄 Если сообщение с отчетами уже существует – просто обновляем его
    if REPORT_FILES:
        try:
            document = FSInputFile(file_path)
            caption = f"📄 Доступны отчеты: выберите нужный файл."

            await bot.edit_message_media(
                chat_id=CHAT_ID,
                message_id=REPORT_FILES,
                media=InputMediaDocument(media=document, caption=caption),
                reply_markup=get_reports_keyboard()
            )
            await message.answer("✅ Файл обновлен и сообщение с отчетом обновлено.")
        except Exception as e:
            logging.error(f"Ошибка при обновлении отчета: {e}")
            await message.answer("⚠ Ошибка при обновлении сообщения. Попробуйте еще раз.")
    else:
        # Если сообщения еще не было, создаем его ОДИН раз
        document = FSInputFile(file_path)
        caption = f"📄 Доступны отчеты: выберите нужный файл."
        msg = await bot.send_document(
            chat_id=CHAT_ID,
            document=document,
            caption=caption,
            message_thread_id=REPORT_TOPIC_ID,
            reply_markup=get_reports_keyboard()
        )
        REPORT_FILES = msg.message_id  # Запоминаем ID

    await message.delete()  # Удаляем сообщение с командой, чтобы не засорять чат

# 📄 **Обработчик кнопок (редактирует существующее сообщение)**
@router.callback_query(lambda c: c.data in ["show_events_report", "show_finance_report"])
async def report_callback_handler(callback: types.CallbackQuery):
    global REPORT_FILES

    report_type = "events" if callback.data == "show_events_report" else "finance"
    file_path = os.path.join(REPORTS_DIR, f"{report_type}.pdf")

    if not os.path.exists(file_path):
        await callback.answer("❌ Отчет не найден. Администратор должен загрузить новый файл.", show_alert=True)
        return

    document = FSInputFile(file_path)
    caption = f"📄 Доступны отчеты: выберите нужный файл."

    # 🔄 Всегда редактируем сообщение, а не создаем новое
    if REPORT_FILES:
        try:
            await callback.bot.edit_message_media(
                chat_id=CHAT_ID,
                message_id=REPORT_FILES,
                media=InputMediaDocument(media=document, caption=caption),
                reply_markup=get_reports_keyboard()
            )
        except Exception as e:
            logging.error(f"Ошибка при обновлении отчета: {e}")
            await callback.answer("⚠ Ошибка обновления сообщения, попробуйте позже.", show_alert=True)

    await callback.answer()

# 🔹 Кнопки для Правил и FAQ
def get_rules_faq_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📜 Правила", callback_data="show_rules")],
            [InlineKeyboardButton(text="❓ FAQ", callback_data="show_faq")]
        ]
    )

# 🔹 Тексты для кнопок
FAQ_DATA = {
    "show_rules": "📜 **Правила сообщества:**\n\n1️⃣ Будьте вежливыми\n2️⃣ Не спамьте\n3️⃣ Соблюдайте правила чата\n\nСпасибо за понимание! ✅",
    "show_faq": "❓ **Часто задаваемые вопросы:**\n\n🔹 *Как оплатить?* - Перейдите в раздел 'Реквизиты'.\n🔹 *Как получить доступ?* - Напишите администратору.\n🔹 *Как поддержать проект?* - Внести 1000 сом в фонд библиотеки.\n\nЕсли остались вопросы, напишите админу. 😉"
}

# ✅ Отправка меню в топик "Правила"
async def send_faq_menu(bot: Bot):  # Изменили types.Bot -> Bot
    await bot.send_message(
        chat_id=CHAT_ID,
        text="📢 Добро пожаловать! Выберите раздел:",
        reply_markup=get_rules_faq_keyboard(),
        message_thread_id=FAQ_TOPIC_ID
    )

# ✅ Автоматически показываем меню при новом сообщении в топике "Правила"
@router.message(lambda message: message.message_thread_id == FAQ_TOPIC_ID)
async def auto_faq_menu(message: types.Message):
    await message.answer("📢 Выберите раздел:", reply_markup=get_rules_faq_keyboard())

# ✅ Обработчик кнопок без отправки нового сообщения
@router.callback_query(lambda c: c.data in FAQ_DATA)
async def faq_callback_handler(callback: types.CallbackQuery):
    new_text = FAQ_DATA[callback.data]  # Получаем текст по callback_data
    await callback.message.edit_text(new_text, reply_markup=get_rules_faq_keyboard(), parse_mode="Markdown")
    await callback.answer()

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

@router.message(lambda message: message.message_thread_id == TOPICS.get("онас"))
async def auto_about_menu(message: Message):
    """Автоматически показывает меню, если кто-то пишет в топик 'О нас'."""
    topic_id = TOPICS["онас"]
    logging.info(f"📌 В топике 'О нас' появилось новое сообщение от {message.from_user.username}. Отправляем меню.")
    await message.answer("📢 Выберите раздел:", reply_markup=get_about_us_keyboard())

# 🔹 Обработчики кнопок с `edit_message_text`
@router.callback_query(lambda c: c.data.startswith("about_"))
async def about_callback_handler(callback: types.CallbackQuery):
    """Редактирует сообщение с кнопками только для пользователя, который нажал"""
    responses = {
        "about_video": ("🎥 Видео о нашем проекте\n больше выидео найдете по сыылке -> https://drive.google.com/drive/folders/1CmsFgQQVetcUBFw8XcanelkNwxSBJjvm", "about_project.mp4"),
        "about_photo": ("🖼 Фото о нашем проекте\n Галерея фото -> https://drive.google.com/drive/folders/1CXIOPapS8w06fJtm1KGbzjw5pgZ_nZhK", "photo.jpg"),
        "about_projects": (
        "📂 **Наши проекты:**\n\n"
        "1️⃣ **Дем-ивент** – Биздин китепкана башка китепканалардан айырмаланып жашоосу кызыктуу болуусу үчүн ар дайым ар кандай форматтагы иш-чараларды уюштуруп келет.\n\n"
        "2️⃣ **Дем-ыктыярчы** – Коомубуздагы баардык жаштарды өзгөртө албарыбыз анык, бирок бир инсандын өзгөрүүсүнө түрткү боло алсак, ал адам дагы башкаларга таасир берет. "
        "Ошол себептүү 14-18 жаштагы окуучулар менен аларга кызыктуу болгон багыттар боюнча өзүн-өзү өнүктүрүү программасын иштеп чыгып иш алып баруудабыз.\n\n"
        "3️⃣ **Лидер мугалим** – Акыркы мезгилде мугалимдердин коомдогу орду төмөндөп кеткен көрүнүшкө күбө болуудабыз. "
        "Бул долбоордун негизги максаты мугалимдердин беделин алардын кесипкөйлүгүн күчөтүү, өзүн-өзү өнүктүрүүсү аркылуу көтөрүү.",
        "projects.jpg"
    ),
        "about_history": ("📜 **История проекта**:\nНаш проект был создан в ... (тут можно добавить описание).", "history.jpg"),
    }

    # text, image_filename = responses.get(callback.data, "Ошибка, попробуйте снова.")
    response = responses.get(callback.data)
    
    if response is None:
        await callback.answer("❌ Ошибка: неверный запрос", show_alert=True)
        return

    text, file_name = response

    file_path = os.path.join(ASSETS_DIR, file_name)

    # Проверяем, существует ли файл
    if not os.path.exists(file_path):
        await callback.answer("❌ Файл не найден!", show_alert=True)
        return

    media_file = FSInputFile(file_path)

    # Улучшенная проверка формата файла (независимо от регистра)
    if file_name.lower().endswith((".jpg", ".jpeg", ".png")):
        media = InputMediaPhoto(media=media_file, caption=text)
    elif file_name.lower().endswith((".mp4", ".mov", ".avi", ".mkv")):
        media = InputMediaVideo(media=media_file, caption=text)
    else:
        await callback.answer("❌ Неподдерживаемый формат файла", show_alert=True)
        return

    try:
        await callback.message.edit_media(media, reply_markup=get_about_us_keyboard())
    except Exception as e:
        await callback.answer(f"⚠ Ошибка при обновлении медиа: {str(e)}", show_alert=True)

    await callback.answer()


@router.message(Command("send"))
async def send_to_topic(message: types.Message):
    logging.info(f"📥 Получена команда /send от {message.from_user.username}: {message.text}")

    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет прав на отправку сообщений.")
        return

    # Если сообщение содержит фото, видео или документ — берем caption, иначе обычный текст
    raw_text = message.caption if message.caption else message.text

    if not raw_text:
        await message.answer("❌ Укажите текст сообщения после команды /send.")
        return

    args = raw_text.split(maxsplit=2)

    if len(args) < 3:
        await message.answer("❌ Используйте формат: /send [топик] [текст]")
        return

    topic_name = args[1].lower()
    text = args[2]

    if topic_name not in TOPICS:
        await message.answer(f"❌ Такого топика нет. Доступные: {', '.join(TOPICS.keys())}")
        return

    topic_id = TOPICS[topic_name]

    # Если топик "general", `message_thread_id` не нужен
    message_kwargs = {"chat_id": CHAT_ID, "caption": text}
    if topic_name != "general":
        message_kwargs["message_thread_id"] = topic_id

    # Отправка медиа (фото, видео, документ)
    if message.photo:
        await message.bot.send_photo(**message_kwargs, photo=message.photo[-1].file_id)
    elif message.video:
        await message.bot.send_video(**message_kwargs, video=message.video.file_id)
    elif message.document:
        await message.bot.send_document(**message_kwargs, document=message.document.file_id)
    elif message.voice:
        await message.bot.send_voice(**message_kwargs, voice=message.voice.file_id)

    else:
        # Если нет медиа, отправляем текст
        await message.bot.send_message(CHAT_ID, text, message_thread_id=topic_id if topic_name != "general" else None)

    await message.answer(f"✅ Сообщение отправлено в **{topic_name}**!")


# Напоминание 
async def auto_send_payment_reminder(bot: Bot):
    """Авто-напоминание о платеже"""
    topic_id = TOPICS["general"]

    today = datetime.datetime.now().day
    if today == 18:
        await bot.send_message(CHAT_ID, PAYMENT_REMINDER)
        logging.info("📨 Напоминание отправлено ВСЕМ 1-го числа.")
    
    elif today == 25:
        unpaid_users = get_unpaid_users()
        
        if unpaid_users:
            for user_id in unpaid_users:
                await bot.send_message(user_id, "⚠ Напоминание: Вы не оплатили взнос. Пожалуйста, внесите платеж.")
            logging.info(f"📨 Напоминание отправлено {len(unpaid_users)} пользователям, которые не заплатили.")
        else:
            logging.info("✅ Все заплатили, напоминание 5-го числа не требуется.")
    else:
        logging.info("📅 Сегодня не 1-е и не 5-е число, напоминание не отправляется.")



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

    def clean_text(value):
        return str(value).strip().replace("\u00A0", " ")  # Убираем пробелы и неразрывные пробелы

    # 🔍 Проверяем, есть ли платеж в Google Sheets
    records = [{k.strip(): v for k, v in row.items()} for row in sheet.get_all_records()]  # Убираем лишние пробелы
    row_number = None

    for i, row in enumerate(records, start=2):  # Первая строка — заголовки
        logging.info(f"🔍 Проверяем строку {i}: {row}")  # 🔹 Логируем все строки
        if clean_text(row["Telegram ID"]) == clean_text(user_id) and clean_text(row["Сумма"]) == clean_text(amount):
            row_number = i
            break

    if row_number is None:
        logging.warning(f"❌ Платеж не найден! user_id={user_id}, amount={amount}")
        await callback.answer("❌ Платеж не найден в Google Sheets!", show_alert=True)
        return
    time.sleep(0.5) 

    # 🔹 Обновляем статус платежа в Google Sheets
    if action == "confirm":
        sheet.update_acell(f"F{row_number}", "✅ Подтвержден")  # Колонка "Статус"
        await callback.message.edit_caption(
            f"✅ Чек от @{callback.from_user.username} подтвержден!",
            reply_markup=None
        )
        await sponsor_bot.send_message(user_id, "✅ Ваш платеж подтвержден!")
        logging.info(f"✅ Чек от user_id={user_id} на сумму {amount} сом подтвержден!")

    elif action == "reject":
        sheet.update_acell(f"F{row_number}", "❌ Отклонен")  # Колонка "Статус"
        await callback.message.edit_caption(
            f"❌ Чек от @{callback.from_user.username} отклонен!",
            reply_markup=None
        )
        await sponsor_bot.send_message(user_id, "❌ Ваш платеж отклонен. Попробуйте отправить другой чек.")
        logging.info(f"❌ Чек от user_id={user_id} на сумму {amount} сом отклонен!")

    await callback.answer()