import gspread
from google.oauth2.service_account import Credentials
from flask import Flask, render_template, jsonify, send_file
import random
import csv
import os
import threading
import time
from datetime import datetime

app = Flask(__name__)

DATA_FILE = "work_bay_data.csv"

# ================= GOOGLE SHEETS SETUP =================
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

if os.path.exists("credentials.json"):
   import json
   import os

    creds_dict = json.loads(os.environ.get("GOOGLE_CREDENTIALS"))
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open_by_key("1cKFkT8cycikiK4rPTxJfJX-zgqmP5Kdcd3izSm8bXis").sheet1
else:
    sheet = None

# ================= CREATE CSV =================
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Time", "Voltage", "Current", "Power", "Energy", "Frequency", "PF"])

total_energy = 0
latest_data = {}

def generate_live_data():
    global total_energy, latest_data

    while True:
        now = datetime.now()
        hour = now.hour

        if 2 <= hour < 6:
            current = random.uniform(0.5, 2)
        elif 6 <= hour < 9:
            current = random.uniform(5, 10)
        elif 9 <= hour < 13:
            current = random.uniform(10, 18)
        elif 13 <= hour < 15:
            current = random.uniform(4, 8)
        elif 15 <= hour < 17:
            current = random.uniform(8, 14)
        else:
            current = random.uniform(15, 25)

        voltage = random.uniform(245, 260)
        power = voltage * current
        frequency = random.uniform(49.8, 50.2)
        pf = random.uniform(0.7, 0.98)

        total_energy += power / 3600000

        data = {
            "Time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "Voltage": round(voltage, 1),
            "Current": round(current, 2),
            "Power": round(power, 1),
            "Energy": round(total_energy, 3),
            "Frequency": round(frequency, 1),
            "PF": round(pf, 2)
        }

        latest_data = data

        with open(DATA_FILE, "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(data.values())

        if sheet:
            sheet.append_row(list(data.values()))

        time.sleep(5)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/data")
def data():
    history = []

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as file:
            reader = csv.DictReader(file)
            history = list(reader)[-20:]

    return jsonify({
        "latest": latest_data,
        "history": history
    })

@app.route("/download")
def download():
    return send_file(DATA_FILE, as_attachment=True)

@app.route("/live-sheet")
def live_sheet():
    rows = []

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as file:
            reader = csv.DictReader(file)
            rows = list(reader)

    return render_template("live_sheet.html", rows=rows)

if __name__ == "__main__":
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        thread = threading.Thread(target=generate_live_data)
        thread.daemon = True
        thread.start()

    app.run(debug=True)
