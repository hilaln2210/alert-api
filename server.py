import requests
import time

# קישור לשליפת כל ההתראות של פיקוד העורף ל־24.06.2025
OREF_URL = "https://alerts-history.oref.org.il/Shared/Ajax/GetAlarmsHistory.aspx?lang=he&fromDate=24.06.2025&toDate=24.06.2025&mode=0"

# קישור לטבלת SheetDB (טבלת Users)
SHEETDB_API = "https://sheetdb.io/api/v1/v88pii4vv3hni"

def fetch_alerts():
    try:
        res = requests.get(OREF_URL)
        res.raise_for_status()
        data = res.json()
        return [a for a in data if a.get("category") == 1]
    except Exception as e:
        print("❌ שגיאה בשליפת התראות:", e)
        return []

def fetch_existing_rids():
    try:
        res = requests.get(SHEETDB_API)
        res.raise_for_status()
        return {entry.get("rid") for entry in res.json() if "rid" in entry}
    except Exception as e:
        print("❌ שגיאה בשליפת rid קיימים מ־SheetDB:", e)
        return set()

def push_new_alerts(new_alerts):
    for alert in new_alerts:
        try:
            # שליחת ההתראה החדשה אל הטבלה
            requests.post(SHEETDB_API, json={"data": alert})
            print(f"✅ נוספה התראה חדשה: {alert['data']} בשעה {alert['time']}")
        except Exception as e:
            print("❌ שגיאה בהוספת התראה:", e)

def main():
    alerts = fetch_alerts()
    if not alerts:
        print("🔄 אין התראות זמינות כרגע.")
        return

    existing_rids = fetch_existing_rids()
    new_alerts = [a for a in alerts if str(a.get("rid")) not in existing_rids]

    if new_alerts:
        print(f"📢 נמצאו {len(new_alerts)} התראות חדשות.")
        push_new_alerts(new_alerts)
    else:
        print("⏸ אין התראות חדשות.")

if __name__ == "__main__":
    while True:
        main()
        time.sleep(60)  # מריץ כל דקה
