import dsbapi

client = dsbapi.DSBApi("177802", "Ado2201")
eintraege = client.fetch_entries()

for i, block in enumerate(eintraege):
    for j, zeile in enumerate(block):
        if "9c" in str(zeile).lower():
            print(f"Treffer in Block {i}, Zeile {j}:", zeile)
            if j + 1 < len(block):
                print("  Naechste Zeile:", block[j + 1])
