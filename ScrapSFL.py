from selenium import webdriver
from selenium.webdriver.firefox.options import Options  # Importer Options pour Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service  # Service pour Firefox
from webdriver_manager.firefox import GeckoDriverManager  # Utilisation de GeckoDriverManager pour Firefox
from selenium.webdriver.remote.webelement import WebElement
from Asset import Asset
from AssetType import AssetType
from AssetSource import AssetSource
import time
import os
from typing import Dict, Union
from datetime import datetime
import requests
from FetchExchangeRates import FetchExchangeRates
import re

def safe_float_convert(s: str) -> float:
    # Mapping des chiffres en exposants Unicode vers int
    subscript_map = {
        '₀': 0, '₁': 1, '₂': 2, '₃': 3, '₄': 4,
        '₅': 5, '₆': 6, '₇': 7, '₈': 8, '₉': 9
    }

    # Match spécial : ex "0.0₅9681"
    match = re.match(r"0\.0([₀₁₂₃₄₅₆₇₈₉])(\d+)", s)
    if match:
        exponent_char = match.group(1)
        digits = match.group(2)
        zeros = subscript_map[exponent_char]
        fixed_str = '0.' + ('0' * zeros) + digits
        return float(fixed_str)
    
    # Cas standard : float normal
    return float(s)

class ScrapSFL:
    def __init__(self, timestamp: str, rates: FetchExchangeRates):
        self.wallet = "0x9c7AaA2876517920041769f0D385f8cBb8893086"
        self.wallet_name = "Main Wallet"
        self.timestamp = timestamp
        
        self.btc_eur = rates.getBtcEur()
        self.btc_usd = rates.getBtcUsd()
        self.usd_eur = rates.getUsdEur()
        
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        # Chemin explicite vers Firefox ESR
        firefox_binary = '/usr/bin/firefox-esr'
        if not os.path.exists(firefox_binary):
            firefox_binary = '/usr/bin/firefox'
        
        options.binary_location = firefox_binary
        
        try:
            # Installation manuelle de geckodriver
            self.driver = webdriver.Firefox(
                options=options,
                service=Service('/usr/local/bin/geckodriver')
            )
        except Exception as e:
            print(f"Erreur lors de l'initialisation du driver: {e}")
            print("Essai avec configuration minimale...")
            
            # Tenter une configuration minimale
            from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
            binary = FirefoxBinary(firefox_binary)
            self.driver = webdriver.Firefox(
                firefox_binary=binary,
                options=options,
                service=Service('/usr/local/bin/geckodriver')
            )
        
        # Ajouter des timeouts plus importants
        self.driver.set_page_load_timeout(180)
        self.driver.implicitly_wait(60)

        self.url = f"https://sfl.world/cost/93357"
        print(f"Ouverture de l'URL: {self.url}")
        self.driver.get(self.url)

        print("Attente du chargement de la page...")
        time.sleep(30)

        self.hold_data = {}
        self.defi_data = {}
    
    def getFarmValueInDollar(self):
        value
        
        try:
            value = self.driver.find_element(By.TAG_NAME, "h4").text
                
        except Exception as e:
            print("Erreur lors du chargement du h4 : ", e)
        
        return value

    def getHoldAssets(self, hold_data: Dict[str, Dict[str, Union[str, float]]] ):
        btc_tickers = {"BTC", "CBBTC", "WBTC"}
        usd_stables = {"USDC", "USDT", "USR", "DAI", "USDC.E", "USDT.E", "USD₮0"}
        eur_stables = {"EURC"}
        
        assets_list = []
        for ticker in hold_data:
            ticker_upper = ticker.upper()
            price = hold_data[ticker]['price']
            amount = hold_data[ticker]['amount']
            if ticker_upper in btc_tickers:
                assets_list.append(Asset(ticker, AssetType.BTC, AssetSource.EVM, self.timestamp, "USD", self.usd_eur, self.btc_eur, self.btc_usd, amount, price, amount * price, ticker, wallet_name = self.wallet_name))
            elif ticker_upper in usd_stables:
                assets_list.append(Asset(ticker, AssetType.FIAT, AssetSource.EVM, self.timestamp, "USD", self.usd_eur, self.btc_eur, self.btc_usd, amount, price, amount * price, ticker, wallet_name = self.wallet_name))
            elif ticker_upper in eur_stables:
                assets_list.append(Asset(ticker, AssetType.FIAT, AssetSource.EVM, self.timestamp, "USD", self.usd_eur, self.btc_eur, self.btc_usd, amount, price, amount * price, ticker, wallet_name = self.wallet_name))
            else:
                assets_list.append(Asset(ticker, AssetType.ALTCOIN, AssetSource.EVM, self.timestamp, "USD", self.usd_eur, self.btc_eur, self.btc_usd, amount, price, amount * price, ticker, wallet_name = self.wallet_name))
            
        return assets_list

    def getDeFiAssets(self, defi_data):
        assets_list = []
        
        for data in defi_data:
            assets_list.append(Asset(data["Protocol"], AssetType.DEFI, AssetSource.SUI, self.timestamp, "USD", self.usd_eur, self.btc_eur, self.btc_usd, value = float(data["Value"]), wallet_name = self.wallet_name, defi_type = data["DeFi Type"]))
        return assets_list
        
    def kill(self):
        # Fermer le navigateur
        self.driver.quit()
        
if __name__ == "__main__":

        assets_list = []
        
        wallet_address = "0xb9cd25f3777db149c61ce62a819dd4ad4935399095998a1e4b406d7d3979cb0a"
        rates = FetchExchangeRates()
        scraping = ScrapSFL("0", rates)
        
        print(scraping.getFarmValueInDollar())
        
        scraping.kill()
        
        print(f"Total assets to insert: {len(assets_list)}")
