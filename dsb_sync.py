import datetime
import pytz
from icalendar import Calendar, Event
import dsbapi

# ================= EINSTELLUNGEN =================
DSB_USER = "177802"          
DSB_PASS = "Ado2201"     
MEINE_KLASSE = "9C"               

STUNDENZEITEN = {
    1: ("08:00", "08:45"),
    2: ("08:50", "09:35"),
    3: ("09:55", "10:40"),
    4: ("10:45", "11:30"),
    5: ("11:50", "12:35"),
    6: ("12:40", "13:25"),
    7: ("13:30", "14:15"),
    8: ("14:20", "15:05"),
}
 =================================================

def erstelle_kalender():
    client = dsbapi.DSBApi(DSB_USER, DSB_PASS)
    eintraege_listen = client.fetch_entries()

    cal = Calendar()
    cal.add('prodid', '-//DSBmobile Sync//DE')
    cal.add('version', '2.0')
    tz = pytz.timezone('Europe/Berlin')

    gefundene_entfaelle = 0

    for tabelle in eintraege_listen:
        for eintrag in tabelle:
            klasse = str(eintrag.get('class', ''))
            art = str(eintrag.get('type', '')).lower()
            datum_str = str(eintrag.get('date', ''))
            stunde_str = str(eintrag.get('lesson', ''))
            fach = str(eintrag.get('subject', 'Unbekannt'))
            text = str(eintrag.get('text', ''))

            if MEINE_KLASSE.lower() in klasse.lower() and ("entfall" in art or "frei" in art or "entfall" in text.lower()):
                try:
                    tag, monat, jahr = map(int, datum_str.split('.'))
                    datum = datetime.date(jahr, monat, tag)

                    stunden = [int(s.strip()) for s in stunde_str.replace('-', ',').split(',') if s.strip().isdigit()]
                    if not stunden:
                        continue

                    start_stunde = min(stunden)
                    end_stunde = max(stunden)

                    if start_stunde not in STUNDENZEITEN or end_stunde not in STUNDENZEITEN:
                        continue

                    start_zeit = datetime.datetime.strptime(STUNDENZEITEN[start_stunde][0], "%H:%M").time()
                    end_zeit = datetime.datetime.strptime(STUNDENZEITEN[end_stunde][1], "%H:%M").time()

                    start_dt = tz.localize(datetime.datetime.combine(datum, start_zeit))
                    end_dt = tz.localize(datetime.datetime.combine(datum, end_zeit))

                    event = Event()
                    event.add('summary', f"❌ ENTFALL: {fach} ({stunde_str}. Std)")
                    event.add('dtstart', start_dt)
                    event.add('dtend', end_dt)
                    event.add('description', f"Art: {eintrag.get('type')}\nHinweis: {text}")
                    event.add('uid', f"dsb-{datum_str}-{stunde_str}-{fach}@dsbsync")

                    cal.add_component(event)
                    gefundene_entfaelle += 1

                except Exception as e:
                    print(f"Eintrag übersprungen wegen Formatierungsfehler: {e}")

    with open('entfaelle.ics', 'wb') as f:
        f.write(cal.to_ical())

    print(f"Fertig! {gefundene_entfaelle} Entfälle in 'entfaelle.ics' gespeichert.")

if __name__ == "__main__":
    erstelle_kalender()
  
