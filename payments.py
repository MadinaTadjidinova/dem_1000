import pytesseract
from PIL import Image
from aiogram import types, Router
from config import CHAT_ID, ADMIN_CHAT_ID

router = Router()  # Используем Router

def extract_text_from_image(image_path):
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img, lang="eng+rus")
    return text

def validate_receipt(image_path, expected_amount):
    text = extract_text_from_image(image_path)
    if str(expected_amount) not in text:
        return False, "Сумма не найдена в чеке."
    return True, "Чек подтверждён."

@router.message()
async def pay_handler(message: types.Message):
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

    # Получаем файл чека
    file_id = message.photo[-1].file_id
    file_info = await message.bot.get_file(file_id)
    file_path = file_info.file_path
    local_path = f"receipts/{file_id}.jpg"

    # Скачиваем фото чека
    await message.bot.download_file(file_path, local_path)

    # Проверяем чек
    is_valid, validation_message = validate_receipt(local_path, amount)

    if is_valid:
        await message.answer(f"✅ Чек автоматически подтверждён! Сумма: {amount} сом.")
    else:
        await message.bot.send_photo(ADMIN_CHAT_ID, photo=open(local_path, "rb"), caption=f"❗ Подозрительный чек от @{message.from_user.username}.\nПричина: {validation_message}")
        await message.answer("🔍 Ваш чек отправлен на проверку админам. Ожидайте подтверждения.")
