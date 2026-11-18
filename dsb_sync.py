import datetime
import pytz
from icalendar import Calendar, Event
import dsbapi

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

def erstelle_kalender():
    client = dsbapi.DSBApi(DSB_USER, DSB_PASS)
    eintraege_listen = client.fetch_entries()

    cal = Calendar()
    cal.add('prodid', '-//DSBmobile Sync//DE')
    cal.add('version', '2.0')
    tz = pytz.timezone('Europe/Berlin')

    gefundene_eintraege = 0

    for tabelle in eintraege_listen:
        for eintrag in tabelle:
            klasse = str(eintrag.get('class', ''))
            art = str(eintrag.get('type', 'Aenderung')).strip()
            datum_str = str(eintrag.get('date', ''))
            stunde_str = str(eintrag.get('lesson', ''))
            fach = str(eintrag.get('subject', 'Unbekannt')).strip()
            raum = str(eintrag.get('room', '')).strip()
            vertreter = str(eintrag.get('new_teacher', '')).strip()
            text = str(eintrag.get('text', '')).strip()

            if MEINE_KLASSE.lower() in klasse.lower():
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

                    ist_entfall = "entfall" in art.lower() or "frei" in art.lower() or "entfall" in text.lower()
                    titel_prefix = "ENTFALL" if ist_entfall else art.upper()

                    details = [f"Art: {art}"]
                    if vertreter:
                        details.append(f"Vertretung: {vertreter}")
                    if raum:
                        details.append(f"Raum: {raum}")
                    if text:
                        details.append(f"Hinweis: {text}")

                    event = Event()
                    event.add('summary', f"{titel_prefix}: {fach} ({stunde_str}. Std)")
                    event.add('dtstart', start_dt)
                    event.add('dtend', end_dt)
                    if raum:
                        event.add('location', raum)
                    event.add('description', "\n".join(details))
                    event.add('uid', f"dsb-{datum_str}-{stunde_str}-{fach}-{art}@dsbsync")

                    cal.add_component(event)
                    gefundene_eintraege += 1

                except Exception as e:
                    print(f"Eintrag uebersprungen: {e}")

    with open('entfaelle.ics', 'wb') as f:
        f.write(cal.to_ical())

    print(f"Fertig! {gefundene_eintraege} Eintraege gespeichert.")

if __name__ == "__main__":
    erstelle_kalender()
