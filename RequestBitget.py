import requests
import time
import hmac
import hashlib
import base64
from datetime import datetime
import json
from dotenv import load_dotenv
import os
from Asset import Asset
from AssetType import AssetType
from AssetSource import AssetSource

class RequestBitget:
    def __init__(self, timestamp):
        
        load_dotenv()
        self.BASE_URL = "https://api.bitget.com"
        self.API_KEY = os.getenv("BITGET_API_KEY")
        self.API_SECRET = os.getenv("BITGET_API_SECRET")
        self.API_PASSPHRASE = os.getenv("BITGET_API_PASSPHRASE")
        self.timestamp = timestamp
        
        response1 = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=eur")
        response1.raise_for_status()
        self.btc_eur = response1.json()["bitcoin"]["eur"]


        response2 = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd")
        response2.raise_for_status()
        self.btc_usd = response2.json()["bitcoin"]["usd"]

        self.usd_eur = self.btc_eur / self.btc_usd
        


    def get_headers(self, method, request_path, body=""):
        timestamp = str(int(time.time() * 1000))
        prehash = f"{timestamp}{method}{request_path}{body}"
        sign = hmac.new(self.API_SECRET.encode(), prehash.encode(), hashlib.sha256).digest()
        sign_b64 = base64.b64encode(sign).decode()

        return {
            "ACCESS-KEY": self.API_KEY,
            "ACCESS-SIGN": sign_b64,
            "ACCESS-TIMESTAMP": timestamp,
            "ACCESS-PASSPHRASE": self.API_PASSPHRASE,
            "Content-Type": "application/json"
        }

    def get_balances(self):
        url = "/api/spot/v1/account/assets"
        headers = self.get_headers("GET", url)
        response = requests.get(self.BASE_URL + url, headers=headers)
        print("Status code:", response.status_code)
        try:
            data = response.json()
            with open("bitget_assets_response.json", "w") as f:
                json.dump(response.json(), f, indent=4)
        except Exception as e:
            print("Erreur parsing JSON:", e)
            return None
        return data.get("data", None)

    def get_usdt_price(self, symbol):
        url = f"https://api.bitget.com/api/v2/mix/market/symbol-price?productType=usdt-futures&symbol={symbol}USDT"

        response = requests.get(url)
        response.raise_for_status()  # Vérifie si le statut HTTP est 200
        data = response.json()
        price = float(data['data'][0]['price'])
        return price
        


    def fetch_assets_snapshot(self):
        balances = self.get_balances()
        snapshot = []
        for asset in balances:
            ticker = asset["coinName"]
            amount = float(asset["available"])
            if amount == 0.0:
                continue
            if ticker == "USDT":
                price = 1.0
            else:
                price = self.get_usdt_price(ticker)
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
    
    def getHoldAssets(self, hold_data):
        btc_tickers = {"BTC", "CBBTC", "WBTC"}
        usd_stables = {"USDC", "USDT", "USR", "DAI", "USDC.E", "USDT.E", "USD₮0"}
        eur_stables = {"EURC"}
        
        assets_list = []
        for token in hold_data:
            ticker = token['ticker']
            price = token['price_usdt']
            amount = token['amount']
            value = token['total_value_usdt']
            if ticker in btc_tickers:
                assets_list.append(Asset(ticker, AssetType.BTC, AssetSource.BITGET, self.timestamp, "USD", self.usd_eur, self.btc_eur, self.btc_usd, amount, price, value, ticker = ticker))
            elif ticker in usd_stables:
                assets_list.append(Asset(ticker, AssetType.FIAT, AssetSource.BITGET, self.timestamp, "USD", self.usd_eur, self.btc_eur, self.btc_usd, amount, price, value, ticker = ticker))
            elif ticker in eur_stables:
                assets_list.append(Asset(ticker, AssetType.FIAT, AssetSource.BITGET, self.timestamp, "USD", self.usd_eur, self.btc_eur, self.btc_usd, amount, price, value, ticker = ticker))
            else:
                assets_list.append(Asset(ticker, AssetType.ALTCOIN, AssetSource.BITGET, self.timestamp, "USD", self.usd_eur, self.btc_eur, self.btc_usd, amount, price, value, ticker = ticker))
            
        return assets_list

if __name__ == "__main__":
    request = RequestBitget("0")
    #assets_data = request.fetch_assets_snapshot()
    #print(assets_data)
    #assets_list = request.getHoldAssets(assets_data)
    #print(assets_list)
    print("btc/eur :", request.btc_eur)
    print("btc/usd :", request.btc_usd)
    print("usd/eur :", request.usd_eur)
