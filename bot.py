import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import TOKEN
from handlers import router as handlers_router, auto_send_payment_reminder  # ✅ Переименовали router
from payments import router as payments_router  # ✅ Переименовали router

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ✅ Добавляем все обработчики (исключаем дублирование)
dp.include_router(handlers_router)
dp.include_router(payments_router)

async def main():
    logging.basicConfig(level=logging.INFO)
    asyncio.create_task(auto_send_payment_reminder(bot))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
