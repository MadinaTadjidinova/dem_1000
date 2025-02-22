import logging
import gspread
from google.oauth2.service_account import Credentials

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 🔹 Подключаемся к Google Sheets
SHEET_ID = "1pFCN-Ca0hiquICvEbSHndymcNCOyosjjZ624_ZYOkzc"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).sheet1

# ✅ Функция записи платежей
def add_payment(user_id, username, amount, method, status="Ожидание"):
    from datetime import datetime
    date = datetime.now().strftime("%Y-%m-%d %H:%M")
    sheet.append_row([date, username, user_id, amount, method, status])

# ✅ Функция обновления статуса платежа
def update_payment_status(user_id, amount, status):
    logging.info(f"🔍 update_payment_status вызван с user_id={user_id}, amount={amount}, status={status}")

    records = [{k.strip(): v for k, v in row.items()} for row in sheet.get_all_records()]  # Убираем лишние пробелы

    for i, row in enumerate(records, start=2):
        if str(row["Telegram ID"]) == str(user_id) and str(row["Сумма"]) == str(amount):
            logging.info(f"✅ Найден платеж! Обновляем статус на {status}")
            sheet.update_cell(i, 6, status)
            return True

    logging.info("❌ Платеж не найден! Проверь ID и сумму.")
    return False