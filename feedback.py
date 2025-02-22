from aiogram import Router, types
from aiogram.filters import Command, CommandObject  # ✅ Импортируем Command
from config import sponsor_bot, admin_bot, ADMIN_CHAT_ID

router = Router()

FEEDBACK_TOPIC_ID = 238  # ID топика Feedback

@router.message(Command("feedback"))
async def send_feedback_to_admins(message: types.Message, command: CommandObject):
    """Пересылаем отзыв в топик Feedback админской группы в одном сообщении"""
    feedback_text = command.args  # Получаем аргументы команды (текст отзыва)

    if not feedback_text:
        await message.answer("❌ Используйте команду в формате:\n`/feedback Ваш отзыв`", parse_mode="Markdown")
        return

    # Формируем сообщение для админов
    feedback_message = (
        f"📩 *Новый отзыв от пользователя!*\n\n"
        f"👤 *Пользователь:* [{message.from_user.full_name}](tg://user?id={message.from_user.id})\n"
        f"💬 *Сообщение:*\n{feedback_text}"
    )

    # Отправляем в топик Feedback
    await admin_bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=feedback_message,
        parse_mode="Markdown",
        message_thread_id=FEEDBACK_TOPIC_ID  # Указываем ID топика Feedback
    )

    # Подтверждаем пользователю
    await message.answer("✅ Ваш отзыв отправлен администраторам. Спасибо за обратную связь!")
