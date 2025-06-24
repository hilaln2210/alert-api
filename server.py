from flask import Flask, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def get_alerts():
    today = datetime.now().strftime('%d.%m.%Y')
    url = f"https://alerts-history.oref.org.il/Shared/Ajax/GetAlarmsHistory.aspx?lang=he&fromDate={today}&toDate={today}&mode=0"
    
    print(f"[{datetime.now()}] Fetching data from: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # סינון רק התראות מסוג category 1
        filtered_alerts = [alert for alert in data if alert.get("category") == 1]

        print(f"[{datetime.now()}] Fetched {len(filtered_alerts)} alerts of category 1.")
        return jsonify(filtered_alerts)
    
    except requests.RequestException as e:
        print(f"[{datetime.now()}] Error fetching alerts: {e}")
        return jsonify({"error": "Failed to fetch alerts"}), 500

if __name__ == '__main__':
    app.run()
