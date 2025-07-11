import requests

class FetchExchangeRates:
    def __init__(self):
        
        response_btc_eur = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=eur")
        response_btc_eur.raise_for_status()

        response_btc_usd = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd")
        response_btc_usd.raise_for_status()
        
        self.btc_eur = response_btc_eur.json()["bitcoin"]["eur"]
        
        self.btc_usd = response_btc_usd.json()["bitcoin"]["usd"]
        
        self.usd_eur = self.btc_eur / self.btc_usd

    def getBtcEur(self):
        return self.btc_eur
    def getBtcUsd(self):
        return self.btc_usd
    def getUsdEur(self):
        return self.usd_eur