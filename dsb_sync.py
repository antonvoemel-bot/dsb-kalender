import dsbapi

DSB_USER = "177802"
DSB_PASS = "Ado2201"

client = dsbapi.DSBApi(DSB_USER, DSB_PASS)
print("Methoden:", [m for m in dir(client) if not m.startswith("_")])

eintraege = client.fetch_entries()
print("Typ:", type(eintraege), "Laenge:", len(eintraege))
for i, eintrag in enumerate(eintraege[:3]):
    print(f"--- Block {i} ---")
    print(str(eintrag)[:1000])
