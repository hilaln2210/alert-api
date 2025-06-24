from flask import Flask, jsonify
import requests
import datetime

app = Flask(__name__)

@app.route('/')
def get_alerts():
    today = datetime.datetime.now().strftime('%d.%m.%Y')
    url = f'https://alerts-history.oref.org.il/Shared/Ajax/GetAlarmsHistory.aspx?lang=he&fromDate={today}&toDate={today}&mode=0'

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        filtered_alerts = [item for item in data if item.get("category") == 1]
        return jsonify({'alerts': filtered_alerts})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
