import os
import json
from flask import Flask, jsonify, render_template
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

app = Flask(__name__)

SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
if not SPREADSHEET_ID:
    raise ValueError("❌ Ошибка: SPREADSHEET_ID не найдено!")

GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")
if not GOOGLE_CREDENTIALS_JSON:
    raise ValueError("❌ Ошибка: GOOGLE_CREDENTIALS_JSON не найдено!")

try:
    creds_dict = json.loads(GOOGLE_CREDENTIALS_JSON)
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n").strip()
    creds = Credentials.from_service_account_info(creds_dict)
except Exception as e:
    raise ValueError(f"❌ Ошибка подключения к Google Sheets: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stats')
def get_stats():
    # Поднимаем сервис Google Sheets
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    # Читаем все данные от A до Z
    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='A1:Z'
    ).execute()
    values = result.get('values', [])

    # Если нет данных или только заголовок — возвращаем 0
    if not values or len(values) < 2:
        return jsonify({'used': 0})

    headers = values[0]
    rows = values[1:]

    # Находим индекс столбца "Used"
    try:
        used_index = headers.index("Used")
    except ValueError:
        return jsonify({'error': 'Column "Used" not found'}), 400

    # Считаем непустые значения в этом столбце
    used_count = sum(
        1 for row in rows
        if len(row) > used_index and row[used_index].strip()
    )

    return jsonify({'used': used_count})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
