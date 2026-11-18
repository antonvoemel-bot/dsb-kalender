import datetime
import re
import pytz
import requests
from bs4 import BeautifulSoup
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
    plaene = client.fetch_timetable()

    cal = Calendar()
    cal.add('prodid', '-//DSBmobile Sync//DE')
    cal.add('version', '2.0')
    tz = pytz.timezone('Europe/Berlin')

    gefundene_eintraege = 0

    for plan in plaene:
        url = plan.get('url') if isinstance(plan, dict) else getattr(plan, 'url', None)
        if not url:
            continue

        resp = requests.get(url)
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, 'html.parser')

        # Datum aus der Seite suchen (z.B. 19.11.2026)
        text_gesamt = soup.get_text(" ", strip=True)
        datum_match = re.search(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', text_gesamt)
        if not datum_match:
            continue
        tag, monat, jahr = map(int, datum_match.groups())
        datum = datetime.date(jahr, monat, tag)

        aktuelle_klasse = ""

        for zeile in soup.find_all('tr'):
            zellen = [z.get_text(" ", strip=True) for z in zeile.find_all(['td', 'th'])]
            if not zellen or all(z == "" for z in zellen):
                continue

            # Gruppenueberschrift erkennen (z.B. "9C" oder "10A")
            if len(zellen) == 1 or (zellen[0] and all(z == "" for z in zellen[1:])):
                aktuelle_klasse = zellen[0].strip()
                continue

            if MEINE_KLASSE.lower() not in aktuelle_klasse.lower():
                continue

            # Untis-Spalten: 0=Stunde, 1=Vertreter, 2=Fach, 3=Raum, 4=Art/Text...
            stunde_str = zellen[0]
            stunden = [int(s) for s in re.findall(r'\d+', stunde_str)]
            if not stunden:
                continue

            start_stunde = min(stunden)
            end_stunde = max(stunden)
            if start_stunde not in STUNDENZEITEN or end_stunde not in STUNDENZEITEN:
                continue

            vertreter = zellen[1] if len(zellen) > 1 else ""
            fach = zellen[2] if len(zellen) > 2 else "Unbekannt"
            rest = " | ".join([z for z in zellen[3:] if z])

            ist_entfall = ("---" in vertreter or "entfall" in rest.lower() or "frei" in rest.lower())
            prefix = "ENTFALL" if ist_entfall else f"VERTRETUNG ({vertreter})"

            start_zeit = datetime.datetime.strptime(STUNDENZEITEN[start_stunde][0], "%H:%M").time()
            end_zeit = datetime.datetime.strptime(STUNDENZEITEN[end_stunde][1], "%H:%M").time()
            start_dt = tz.localize(datetime.datetime.combine(datum, start_zeit))
            end_dt = tz.localize(datetime.datetime.combine(datum, end_zeit))

            event = Event()
            event.add('summary', f"{prefix}: {fach} ({stunde_str}. Std)")
            event.add('dtstart', start_dt)
            event.add('dtend', end_dt)
            event.add('description', f"Klasse: {aktuelle_klasse}\nVertreter: {vertreter}\nFach: {fach}\nDetails: {rest}")
            event.add('uid', f"dsb-{datum}-{stunde_str}-{fach}-{vertreter}@dsbsync")

            cal.add_component(event)
            gefundene_eintraege += 1

    with open('entfaelle.ics', 'wb') as f:
        f.write(cal.to_ical())

    print(f"Fertig! {gefundene_eintraege} Eintraege gespeichert.")

if __name__ == "__main__":
    erstelle_kalender()
