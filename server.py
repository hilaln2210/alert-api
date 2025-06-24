from flask import Flask, jsonify
import requests

app = Flask(__name__)

@app.route('/api/alerts')
def get_alerts():
    url = "https://alerts-history.oref.org.il/Shared/Ajax/GetAlarmsHistory.aspx"
    params = {
        'lang': 'he',
        'fromDate': '24.06.2025',
        'toDate': '24.06.2025',
        'mode': '0'
    }
    response = requests.post(url, data=params)
    return jsonify(response.json())

if __name__ == '__main__':
    app.run(debug=True)
