import asyncio
import logging
from aiogram import Dispatcher
from config import sponsor_bot, admin_bot
from handlers import router as handlers_router, auto_send_payment_reminder
from payments import pay_router as payments_router

# ✅ Настраиваем глобальное логирование
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

dp_sponsor = Dispatcher()
dp_admin = Dispatcher()

dp_sponsor.include_router(payments_router)
dp_admin.include_router(handlers_router)

async def main():
    logging.info("🔄 Запуск бота...")
    asyncio.create_task(auto_send_payment_reminder(admin_bot))

    await asyncio.gather(
        dp_sponsor.start_polling(sponsor_bot),
        dp_admin.start_polling(admin_bot)
    )

if __name__ == "__main__":
    asyncio.run(main())
