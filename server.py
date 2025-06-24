from flask import Flask, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def get_alerts():
    today = datetime.now().strftime("%d.%m.%Y")
    url = f"https://alerts-history.oref.org.il/Shared/Ajax/GetAlarmsHistory.aspx?lang=he&fromDate={today}&toDate={today}&mode=0"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        filtered_alerts = [alert for alert in data if alert.get('category') == 1]
        return jsonify({"alerts": filtered_alerts})

    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
