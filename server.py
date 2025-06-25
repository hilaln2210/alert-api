# app.py - מערכת VPS מלאה עם SheetDB

from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import json
import time
import threading
from datetime import datetime
import os

app = Flask(**name**)
CORS(app)

# הגדרות SheetDB - עם ה-URLs שלך!

SHEETDB_ALERTS_URL = “https://sheetdb.io/api/v1/hxxnk24a2r05u”  # טבלת Alerts
SHEETDB_USERS_URL = “https://sheetdb.io/api/v1/v88pii4vv3hni”    # טבלת Users

# הגדרות פיקוד העורף

OREF_HISTORY_URL = “https://alerts-history.oref.org.il/Shared/Ajax/GetAlarmsHistory.aspx”
OREF_REALTIME_URL = “https://www.oref.org.il/WarningMessages/alert/alerts.json”

# מצב המערכת

existing_rids = set()
is_monitoring = False
last_check = None
logs = []

def log_message(message, log_type=“info”):
“”“הוספת הודעה ללוג עם timestamp”””
global logs
timestamp = datetime.now().strftime(”%H:%M:%S”)
log_entry = {
“timestamp”: timestamp,
“message”: message,
“type”: log_type,
“id”: len(logs) + 1
}
logs.insert(0, log_entry)
logs = logs[:100]  # שמור רק 100 אחרונים
print(f”[{timestamp}] {message}”)

def fetch_oref_alerts(date_str=None):
“”“שליפת אזעקות מפיקוד העורף”””
if not date_str:
date_str = datetime.now().strftime(”%d.%m.%Y”)

```
url = f"{OREF_HISTORY_URL}?lang=he&fromDate={date_str}&toDate={date_str}&mode=0"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Referer': 'https://www.oref.org.il/'
}

try:
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    alerts = response.json()
    
    # סינון צבע אדום בלבד
    red_alerts = [alert for alert in alerts if alert.get('category') == 1]
    
    log_message(f"📊 נמצאו {len(red_alerts)} אזעקות צבע אדום מתוך {len(alerts)}")
    return red_alerts
    
except Exception as e:
    log_message(f"❌ שגיאה בשליפת אזעקות: {e}", "error")
    return []
```

def fetch_realtime_alerts():
“”“שליפת אזעקות זמן אמת”””
headers = {
‘User-Agent’: ‘Mozilla/5.0’,
‘Referer’: ‘https://www.oref.org.il/’
}

```
try:
    response = requests.get(OREF_REALTIME_URL, headers=headers, timeout=5)
    response.raise_for_status()
    alerts = response.json()
    
    if isinstance(alerts, list) and len(alerts) > 0:
        log_message(f"🚨 אזעקות זמן אמת: {len(alerts)} פעילות", "alert")
        return alerts
    else:
        return []
        
except Exception as e:
    log_message(f"⚠️ שגיאה באזעקות זמן אמת: {e}", "error")
    return []
```

def send_alert_to_sheetdb(alert):
“”“שליחת אזעקה חדשה ל-SheetDB”””
try:
# הכנת הנתונים לטבלה
alert_data = {
“rid”: str(alert.get(“rid”, “”)),
“city”: alert.get(“data”, “”),
“time”: alert.get(“time”, “”),
“date”: alert.get(“date”, “”),
“alertDate”: alert.get(“alertDate”, “”),
“category”: str(alert.get(“category”, “1”)),
“category_desc”: alert.get(“category_desc”, “צבע אדום”),
“matrix_id”: str(alert.get(“matrix_id”, “”))
}

```
    # שליחה ל-SheetDB
    response = requests.post(
        SHEETDB_ALERTS_URL,
        json={"data": [alert_data]},
        timeout=10
    )
    
    if response.status_code in [200, 201]:
        log_message(f"✅ אזעקה נשלחה ל-SheetDB: {alert_data['city']}", "success")
        return True
    else:
        log_message(f"❌ שגיאה בשליחה ל-SheetDB: {response.status_code}", "error")
        return False
        
except Exception as e:
    log_message(f"💥 שגיאה בשליחה ל-SheetDB: {e}", "error")
    return False
```

def update_users_status_in_sheetdb(alert_cities):
“”“עדכון סטטוס משתמשים ב-SheetDB לפי אזעקות”””
try:
# קבלת רשימת משתמשים מ-SheetDB
response = requests.get(SHEETDB_USERS_URL, timeout=10)
if not response.ok:
log_message(“❌ לא ניתן לקבל רשימת משתמשים”, “error”)
return

```
    users = response.json()
    current_time = datetime.now().strftime("%H:%M:%S")
    updated_users = []
    
    for user in users:
        user_city = user.get('city', '').strip()
        user_name = user.get('name', '')
        
        # בדיקה אם העיר של המשתמש מופיעה באזעקות
        city_has_alert = any(
            user_city.lower() in alert_city.lower() or 
            alert_city.lower() in user_city.lower()
            for alert_city in alert_cities if alert_city
        )
        
        if city_has_alert and user.get('status') != 'alarm':
            # עדכון סטטוס המשתמש ל-alarm
            update_data = {
                "status": "alarm",
                "last_updated": current_time
            }
            
            # עדכון ב-SheetDB לפי השם
            update_response = requests.put(
                f"{SHEETDB_USERS_URL}/name/{user_name}",
                json={"data": update_data},
                timeout=10
            )
            
            if update_response.ok:
                updated_users.append(user_name)
    
    if updated_users:
        log_message(f"👥 עודכן סטטוס ל-alarm: {', '.join(updated_users)}", "alert")
    
except Exception as e:
    log_message(f"❌ שגיאה בעדכון משתמשים: {e}", "error")
```

def initialize_users_table():
“”“אתחול טבלת משתמשים עם נתונים ברירת מחדל”””
default_users = [
{“name”: “הילה”, “city”: “תל אביב”, “status”: “ok”, “last_updated”: “”},
{“name”: “נועם”, “city”: “אשדוד”, “status”: “ok”, “last_updated”: “”},
{“name”: “דני”, “city”: “חיפה”, “status”: “ok”, “last_updated”: “”},
{“name”: “שרה”, “city”: “ירושלים”, “status”: “ok”, “last_updated”: “”},
{“name”: “יוסי”, “city”: “אשקלון”, “status”: “ok”, “last_updated”: “”},
{“name”: “לאה”, “city”: “באר שבע”, “status”: “ok”, “last_updated”: “”},
{“name”: “מיכל”, “city”: “נתניה”, “status”: “ok”, “last_updated”: “”}
]

```
try:
    # בדיקה אם הטבלה כבר קיימת
    response = requests.get(SHEETDB_USERS_URL, timeout=10)
    if response.ok:
        existing_users = response.json()
        if len(existing_users) > 0:
            log_message("👥 טבלת משתמשים כבר קיימת", "info")
            return
    
    # יצירת הטבלה עם משתמשים ברירת מחדל
    create_response = requests.post(
        SHEETDB_USERS_URL,
        json={"data": default_users},
        timeout=10
    )
    
    if create_response.ok:
        log_message("👥 טבלת משתמשים נוצרה עם נתונים ברירת מחדל", "success")
    else:
        log_message("❌ שגיאה ביצירת טבלת משתמשים", "error")
        
except Exception as e:
    log_message(f"❌ שגיאה באתחול טבלת משתמשים: {e}", "error")
```

def monitoring_loop():
“”“לולאת המעקב הרציף”””
global is_monitoring, last_check, existing_rids

```
log_message("🚀 מעקב רציף החל", "success")

while is_monitoring:
    try:
        last_check = datetime.now()
        
        # שליפת אזעקות היסטוריות
        today_alerts = fetch_oref_alerts()
        
        # שליפת אזעקות זמן אמת
        realtime_alerts = fetch_realtime_alerts()
        
        # איחוד האזעקות
        all_alerts = today_alerts + realtime_alerts
        
        # חיפוש אזעקות חדשות
        new_alerts = []
        alert_cities = []
        
        for alert in all_alerts:
            rid = str(alert.get("rid", ""))
            if rid and rid not in existing_rids:
                new_alerts.append(alert)
                existing_rids.add(rid)
                alert_cities.append(alert.get("data", ""))
        
        if new_alerts:
            log_message(f"🆕 נמצאו {len(new_alerts)} אזעקות חדשות!", "alert")
            
            # שליחה ל-SheetDB
            for alert in new_alerts:
                send_alert_to_sheetdb(alert)
            
            # עדכון סטטוס משתמשים
            if alert_cities:
                update_users_status_in_sheetdb(alert_cities)
        else:
            log_message("😌 אין אזעקות חדשות", "info")
        
        # המתנה 15 שניות
        time.sleep(15)
        
    except Exception as e:
        log_message(f"💥 שגיאה במעקב: {e}", "error")
        time.sleep(5)  # המתנה קצרה יותר במקרה של שגיאה
```

# API Endpoints

@app.route(’/’)
def home():
“”“דף בית”””
return jsonify({
“service”: “מערכת אזעקות VPS + SheetDB”,
“version”: “1.0”,
“status”: “פעיל”,
“monitoring”: is_monitoring,
“last_check”: last_check.isoformat() if last_check else None,
“total_rids”: len(existing_rids),
“endpoints”: {
“/start”: “התחלת מעקב”,
“/stop”: “עצירת מעקב”,
“/status”: “סטטוס המערכת”,
“/logs”: “לוג פעילות”,
“/test-alerts”: “בדיקת אזעקות ידנית”,
“/init-users”: “אתחול טבלת משתמשים”
}
})

@app.route(’/start’, methods=[‘POST’])
def start_monitoring():
“”“התחלת מעקב רציף”””
global is_monitoring

```
if is_monitoring:
    return jsonify({"success": False, "message": "מעקב כבר פעיל"})

is_monitoring = True

# התחלת thread למעקב
monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
monitoring_thread.start()

log_message("🚀 מעקב רציף הופעל", "success")
return jsonify({"success": True, "message": "מעקב הופעל"})
```

@app.route(’/stop’, methods=[‘POST’])
def stop_monitoring():
“”“עצירת מעקב רציף”””
global is_monitoring

```
if not is_monitoring:
    return jsonify({"success": False, "message": "מעקב לא פעיל"})

is_monitoring = False
log_message("⏸️ מעקב רציף הופסק", "info")

return jsonify({"success": True, "message": "מעקב הופסק"})
```

@app.route(’/status’)
def get_status():
“”“סטטוס המערכת”””
return jsonify({
“success”: True,
“monitoring”: is_monitoring,
“last_check”: last_check.isoformat() if last_check else None,
“total_rids_tracked”: len(existing_rids),
“logs_count”: len(logs),
“server_time”: datetime.now().isoformat(),
“sheetdb_urls”: {
“alerts”: SHEETDB_ALERTS_URL,
“users”: SHEETDB_USERS_URL
}
})

@app.route(’/logs’)
def get_logs():
“”“קבלת לוג פעילות”””
limit = request.args.get(‘limit’, 50, type=int)
return jsonify({
“success”: True,
“logs”: logs[:limit]
})

@app.route(’/test-alerts’)
def test_alerts():
“”“בדיקת אזעקות ידנית”””
log_message(“🔍 בדיקת אזעקות ידנית”, “info”)

```
# בדיקת היסטוריה
today_alerts = fetch_oref_alerts()

# בדיקת זמן אמת
realtime_alerts = fetch_realtime_alerts()

return jsonify({
    "success": True,
    "today_alerts": len(today_alerts),
    "realtime_alerts": len(realtime_alerts),
    "total_rids_tracked": len(existing_rids)
})
```

@app.route(’/init-users’, methods=[‘POST’])
def init_users():
“”“אתחול טבלת משתמשים”””
initialize_users_table()
return jsonify({“success”: True, “message”: “טבלת משתמשים אותחלה”})

@app.route(’/reset-rids’, methods=[‘POST’])
def reset_rids():
“”“איפוס רשימת RIDs (לבדיקות)”””
global existing_rids
existing_rids.clear()
log_message(“🔄 רשימת RIDs אופסה”, “info”)
return jsonify({“success”: True, “message”: “RIDs אופסו”})

if **name** == ‘**main**’:
log_message(“🌟 מערכת VPS+SheetDB מתחילה”)

```
# אתחול טבלת משתמשים
initialize_users_table()

# הפעלת השרת
port = int(os.environ.get('PORT', 10000))
app.run(host='0.0.0.0', port=port, debug=False)
```
