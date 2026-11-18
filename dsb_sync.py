import requests
import dsbapi

orig_get = requests.get
def debug_get(url, *args, **kwargs):
    resp = orig_get(url, *args, **kwargs)
    if "9c" in resp.text.lower():
        idx = resp.text.lower().find("9c")
        print("=== TREFFER IN URL:", url)
        print(resp.text[max(0, idx-200):idx+800])
    return resp

requests.get = debug_get
client = dsbapi.DSBApi("177802", "Ado2201")
client.fetch_entries()


