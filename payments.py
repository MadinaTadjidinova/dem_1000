import os
import pytesseract
from PIL import Image
from aiogram import types, Router
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import admin_bot, ADMIN_CHAT_ID, TOPICS
from google_sheets import add_payment, update_payment_status

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

def get_admin_buttons(user_id, amount):
    """Создаёт inline-кнопки для подтверждения/отклонения чека"""
    buttons = [
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm|{user_id}|{amount}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject|{user_id}|{amount}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

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
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"

    # 📸 Получаем файл чека
    file_id = message.photo[-1].file_id
    file_info = await message.bot.get_file(file_id)
    file_path = file_info.file_path
    local_path = os.path.join(RECEIPTS_FOLDER, f"{file_id}.jpg")

    try:
        await message.bot.download_file(file_path, local_path)
        is_valid, validation_message = validate_receipt(local_path, amount)

        if is_valid:
            add_payment(user_id, username, amount, "Чек", "Подтверждено")
            await message.answer(f"✅ Чек автоматически подтверждён! Сумма: {amount} сом.")
        else:
            add_payment(user_id, username, amount, "Чек (на проверке)", "Ожидание")
            markup = get_admin_buttons(user_id, amount)

            await admin_bot.send_photo(
                chat_id=ADMIN_CHAT_ID,  # ✅ Осталось как есть
                message_thread_id=TOPICS["проверка"],
                photo=FSInputFile(local_path),
                caption=f"❗ Подозрительный чек от @{username}.\nПричина: {validation_message}",
                reply_markup=markup
            )

            await message.answer("🔍 Ваш чек отправлен на проверку админам. Ожидайте подтверждения.")

    except Exception as e:
        await message.answer(f"⚠ Ошибка при обработке чека: {str(e)}")