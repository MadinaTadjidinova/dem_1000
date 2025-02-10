import gspread
from google.oauth2.service_account import Credentials

# 🔹 Подключаемся к Google Sheets
SHEET_ID = "1pFCN-Ca0hiquICvEbSHndymcNCOyosjjZ624_ZYOkzc" 
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

# 📄 Загружаем ключ сервисного аккаунта
creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
client = gspread.authorize(creds)

# 📊 Открываем таблицу
sheet = client.open_by_key(SHEET_ID).sheet1

# ✅ Функция для записи платежей
def add_payment(user_id, username, amount, method):
    from datetime import datetime
    date = datetime.now().strftime("%Y-%m-%d %H:%M")
    sheet.append_row([date, username, user_id, amount, method, "Ожидание"])
    return f"✅ Платёж {amount} сом записан в Google Sheets!"
