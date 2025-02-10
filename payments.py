import os
import pytesseract
from PIL import Image
from aiogram import types, Router
from config import bot, CHAT_ID, ADMIN_CHAT_ID
from google_sheets import add_payment  # ✅ Функция записи в Google Sheets
from aiogram.types import FSInputFile 
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

pay_router = Router()  # ✅ Создаём Router

# ✅ Создаём папку "receipts", если её нет
RECEIPTS_FOLDER = "receipts"
if not os.path.exists(RECEIPTS_FOLDER):
    os.makedirs(RECEIPTS_FOLDER)

def extract_text_from_image(image_path):
    """Считываем текст из изображения с чека."""
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img, lang="eng+rus")
    return text

def validate_receipt(image_path, expected_amount):
    """Проверяем, есть ли сумма на чеке."""
    text = extract_text_from_image(image_path)
    return str(expected_amount) in text, "Сумма не найдена в чеке."

@pay_router.message()
async def pay_handler(message: types.Message):
    """Обрабатываем фото чека от пользователя."""
    
    if not message.photo:
        await message.answer("❌ Отправьте фото чека и укажите сумму в описании.")
        return

    if not message.caption:
        await message.answer("❌ Укажите сумму в описании к изображению.")
        return
    
    args = message.caption.split()
    if len(args) < 1:
        await message.answer("❌ Используйте формат: `1000` (только сумма)")
        return

    amount = args[0]

    # 📸 Получаем файл чека
    file_id = message.photo[-1].file_id
    file_info = await message.bot.get_file(file_id)  # ✅ Исправили `bot` на `message.bot`
    file_path = file_info.file_path
    local_path = os.path.join(RECEIPTS_FOLDER, f"{file_id}.jpg")

    try:
        # 🔽 Скачиваем фото чека
        await message.bot.download_file(file_path, local_path)

        # 🔍 Проверяем чек
        is_valid, validation_message = validate_receipt(local_path, amount)

        if is_valid:
            add_payment(message.from_user.id, message.from_user.username, amount, "Чек")  # ✅ Добавили "Чек" как способ оплаты
            await message.answer(f"✅ Чек автоматически подтверждён! Сумма: {amount} сом.")
        else:
            add_payment(message.from_user.id, message.from_user.username, amount, "Чек (на проверке)")
            await bot.send_photo(
                ADMIN_CHAT_ID,
                photo=FSInputFile(local_path),
                caption=f"❗ Подозрительный чек от @{message.from_user.username}.\nПричина: {validation_message}"
            )

            await message.answer("🔍 Ваш чек отправлен на проверку админам. Ожидайте подтверждения.")

    except Exception as e:
        await message.answer(f"⚠ Ошибка при обработке чека: {str(e)}")
