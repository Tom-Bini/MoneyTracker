import requests
import time
import hmac
import hashlib
import base64
from datetime import datetime
import json

API_KEY = "bg_a282f92c0bbc4fc0a98e1dbb500f0d27"
API_SECRET = "267de3b1df2ae740d37e4ef2342d9a56bca404d50e6cf4cfcf19be8b8e624b7f"
API_PASSPHRASE = "saucissefrite"

BASE_URL = "https://api.bitget.com"

def get_headers(method, request_path, body=""):
    timestamp = str(int(time.time() * 1000))
    prehash = f"{timestamp}{method}{request_path}{body}"
    sign = hmac.new(API_SECRET.encode(), prehash.encode(), hashlib.sha256).digest()
    sign_b64 = base64.b64encode(sign).decode()

    return {
        "ACCESS-KEY": API_KEY,
        "ACCESS-SIGN": sign_b64,
        "ACCESS-TIMESTAMP": timestamp,
        "ACCESS-PASSPHRASE": API_PASSPHRASE,
        "Content-Type": "application/json"
    }

def get_balances():
    url = "/api/spot/v1/account/assets"
    headers = get_headers("GET", url)
    response = requests.get(BASE_URL + url, headers=headers)
    print("Status code:", response.status_code)
    try:
        data = response.json()
        with open("bitget_assets_response.json", "w") as f:
            json.dump(response.json(), f, indent=4)
    except Exception as e:
        print("Erreur parsing JSON:", e)
        return None
    return data.get("data", None)

def get_usdt_price(symbol):
    pair = symbol.upper() + "USDT"
    url = f"{BASE_URL}/api/v2/spot/market/ticker?symbol={pair}"
    response = requests.get(url)
    data = response.json()
    if data.get("code") == "00000":
        return float(data["data"]["close"])
    return None

def fetch_assets_snapshot():
    balances = get_balances()
    snapshot = []
    for asset in balances:
        ticker = asset["coinName"]
        amount = float(asset["available"])
        if amount == 0.0:
            continue
        if ticker == "USDT":
            price = 1.0
        else:
            price = get_usdt_price(ticker)
        if price is None:
            continue  # skip if price not found
        total_value = amount * price
        snapshot.append({
            "ticker": ticker,
            "amount": amount,
            "price_usdt": price,
            "total_value_usdt": total_value
        })
    return snapshot

if __name__ == "__main__":
    assets = fetch_assets_snapshot()
    for asset in assets:
        print(asset)
