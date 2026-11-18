import inspect
import dsbapi

client = dsbapi.DSBApi("177802", "Ado2201")
print(inspect.getsource(client.fetch_entries))

