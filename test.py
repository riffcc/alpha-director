import ipfshttpclient
import inspect
client = ipfshttpclient.connect()
res = client.add('/opt/radio/director/20210523T012515Z', recursive=True)

last_item = res[-1]
print(last_item)
print(type(last_item))
print(inspect.getmembers(last_item))
print(last_item['Hash'])