import requests
import time
from config import probe_key

s = requests.Session()
payloads = [{'key':probe_key, 'temp_C':100.0, 'temp_F':i} for i in [68.0,70.0,72.0,74.0]]
for p in payloads:
    s.post('http://localhost:5000', data=p)
    time.sleep(30)