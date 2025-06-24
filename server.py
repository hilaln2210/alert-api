from flask import Flask, jsonify
import requests

app = Flask(__name__)

@app.route('/')
def get_alerts():
    url = "https://alerts-history.oref.org.il/Shared/Ajax/GetAlarmsHistory.aspx?lang=he&fromDate=24.06.2025&toDate=24.06.2025&mode=0"
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        all_alerts = response.json()
        
        filtered_alerts = [
            alert for alert in all_alerts
            if alert.get('category') == 1
        ]
        
        return jsonify({'alerts': filtered_alerts})
    
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
