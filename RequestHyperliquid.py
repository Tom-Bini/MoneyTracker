from datetime import datetime
import requests
from Asset import Asset
from AssetType import AssetType
from AssetSource import AssetSource
from FetchExchangeRates import FetchExchangeRates
from hyperliquid.info import Info
from hyperliquid.utils import constants
from dotenv import load_dotenv
import os

class RequestHyperliquid:
    def __init__(self, wallet: str, wallet_name: str, timestamp: datetime, rates: FetchExchangeRates):
        self.wallet = wallet
        self.wallet_name = wallet_name
        self.timestamp = timestamp
        load_dotenv()
        self.coingecko_api_key = os.getenv("COINGECKO_API_KEY")
        
        self.btc_eur = rates.getBtcEur()
        self.btc_usd = rates.getBtcUsd()
        self.usd_eur = rates.getUsdEur()
        
    def getHoldings(self):
        info = Info(constants.MAINNET_API_URL, skip_ws=True)
        
        user_staking_summary = info.user_staking_summary(self.wallet)
        total_staked_hype = (float(user_staking_summary["delegated"]) + float(user_staking_summary["undelegated"]) + float(user_staking_summary["totalPendingWithdrawal"]))

        spot_user_state = info.spot_user_state(self.wallet)
        balances = spot_user_state["balances"]

        if balances:
            for balance in balances:
                if balance["coin"] == "HYPE":
                    balance["total"] = float(balance["total"]) + total_staked_hype
        else:
            print("No tokens in spot.")
        return balances
            
    def getHoldAssets(self, balances):
        btc_tickers = {"BTC", "CBBTC", "WBTC", "UBTC"}
        usd_stables = {"USDC", "USDT", "USR", "DAI", "USDC.E", "USDT.E", "USD₮0"}
        eur_stables = {"EURC"}
        
        params = {
            'ids': "hyperliquid",
            'vs_currencies': 'usd',
            'include_market_cap': False,
            'include_24hr_vol': False,
            'include_24hr_change': False,
            'include_last_updated_at': False
            }
        
        try:
            hype_price = requests.get("https://api.coingecko.com/api/v3/simple/price?vs_currencies=usd", params=params)
            hype_price = hype_price.json()
        except Exception as e:
            print(f"Impossible de récup le prix du HYPE via Coingecko: {e}")
        
        
        
        assets_list = []
        
        for balance in balances:
            ticker = balance["coin"]
            amount = float(balance["total"])
            if ticker in btc_tickers:
                price = self.btc_usd
                assets_list.append(Asset(ticker, AssetType.BTC, AssetSource.EVM, self.timestamp, "USD", self.usd_eur, self.btc_eur, self.btc_usd, amount, price, amount * price, ticker, wallet_name = self.wallet_name))
            elif ticker in usd_stables:
                price = 1
                assets_list.append(Asset(ticker, AssetType.FIAT, AssetSource.EVM, self.timestamp, "USD", self.usd_eur, self.btc_eur, self.btc_usd, amount, price, amount * price, ticker, wallet_name = self.wallet_name))
            elif ticker in eur_stables:
                price = 1 / self.usd_eur
                assets_list.append(Asset(ticker, AssetType.FIAT, AssetSource.EVM, self.timestamp, "USD", self.usd_eur, self.btc_eur, self.btc_usd, amount, price, amount * price, ticker, wallet_name = self.wallet_name))
            elif ticker == "HYPE":
                price = hype_price["hyperliquid"]["usd"]
                assets_list.append(Asset(ticker, AssetType.ALTCOIN, AssetSource.EVM, self.timestamp, "USD", self.usd_eur, self.btc_eur, self.btc_usd, amount, price, amount * price, ticker, wallet_name = self.wallet_name))
            
        return assets_list




if __name__ == "__main__":
    
    request = RequestHyperliquid("0x9c7AaA2876517920041769f0D385f8cBb8893086", "test", "0", FetchExchangeRates())
    balances = request.getHoldings()
    request.getHoldAssets(balances)