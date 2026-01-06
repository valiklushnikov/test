import time
import hmac
import hashlib
import requests

API_KEY = "fKwDKXWJH4FovL0zZG="
API_SECRET = "CRAvP1znZ54XrtERWDezPB6FKePT7WYVsVBv-lQQzGUFzPP3Efe36ozs"

timestamp = str(int(time.time() * 1000))
recv_window = "5000"

payload = timestamp + API_KEY + recv_window

signature = hmac.new(
    API_SECRET.encode(),
    payload.encode(),
    hashlib.sha256
).hexdigest()

headers = {
    "X-BAPI-API-KEY": API_KEY,
    "X-BAPI-SIGN": signature,
    "X-BAPI-TIMESTAMP": timestamp,
    "X-BAPI-RECV-WINDOW": recv_window,
}

url = "https://api-testnet.bybit.com/v5/user/query-api"

response = requests.get(url, headers=headers)
print(response.json())