from flask import Flask, jsonify
import requests
from datetime import datetime
import os

app = Flask(__name__)

ALERTS_URL = "https://www.oref.org.il/WarningMessages/alert/alerts.json"
SHEETDB_URL = "https://sheetdb.io/api/v1/v88pii4vv3hni"

def fetch_alerts():
    try:
        response = requests.get(ALERTS_URL)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                alerts = [alert for alert in data if alert.get("category") == 1]
                return alerts
        return []
    except Exception as e:
        print(f"Error fetching alerts: {e}")
        return []

def update_users_with_alerts(alerts):
    try:
        users = requests.get(SHEETDB_URL).json()
        alert_cities = [alert["data"] for alert in alerts]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for user in users:
            if user.get("city") in alert_cities:
                update = {
                    "data": {
                        "last_alert": now,
                        "needs_update": "true"
                    }
                }
                requests.patch(f"{SHEETDB_URL}/name/{user['name']}", json=update)
    except Exception as e:
        print(f"Error updating users: {e}")

@app.route('/')
def index():
    alerts = fetch_alerts()
    update_users_with_alerts(alerts)
    return jsonify({"alerts": alerts})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
