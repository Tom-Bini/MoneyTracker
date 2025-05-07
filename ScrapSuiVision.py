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

class ScrapSuiVision:
    def __init__(self, wallet: str, wallet_name: str, timestamp: str):
        self.wallet = wallet
        self.wallet_name = wallet_name
        self.timestamp = timestamp
        
        response1 = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=eur")
        response1.raise_for_status()
        self.btc_eur = response1.json()["bitcoin"]["eur"]


        response2 = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd")
        response2.raise_for_status()
        self.btc_usd = response2.json()["bitcoin"]["usd"]

        self.usd_eur = self.btc_eur / self.btc_usd
        
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

        self.url = f"https://suivision.xyz/account/{wallet}?tab=Portfolio"
        print(f"Ouverture de l'URL: {self.url}")
        self.driver.get(self.url)

        print("Attente du chargement de la page...")
        time.sleep(15)

        self.hold_data = {}
        self.defi_data = {}
    
    def getHoldingsData(self):
        hold_data = {}
        
        try:
            div_portfolio = self.driver.find_elements(By.CSS_SELECTOR, ".whitespace-nowrap")[2]
            tr_portfolio = div_portfolio.find_elements(By.TAG_NAME, "tr")
            for row in tr_portfolio[1:]:
                price = row.find_element(By.CSS_SELECTOR, "td:nth-child(3)").text
                match = re.search(r"\$([\d.]+)", price)
                if match:
                    extracted_price = match.group(1)
                    # 3. Amount (ex: "1.015621806") → dans la 4e cellule <td>
                    amount_ticker = row.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
                    amount_str, ticker = amount_ticker.split()
                    amount = float(amount_str)
                if price == 0:
                    continue
                elif ticker in hold_data:
                    hold_data[ticker]['amount'] += amount
                    # Le prix peut être mis à jour avec le dernier trouvé
                    hold_data[ticker]['price'] = extracted_price
                else:
                    # Ajouter une nouvelle entrée pour ce ticker
                    hold_data[ticker] = {
                        "ticker": ticker,
                        "price": float(extracted_price),
                        "amount": amount
                    }
                
        except Exception as e:
            print("Erreur lors du chargement des tr : ", e)
            print("Dernière ligne analysée : ", row.text)
        
        return hold_data
        
    def getDeFiPositionsData(self):
        data_list = []

        try:
            main = self.driver.find_element(By.TAG_NAME, 'main')
            sections = main.find_elements(By.TAG_NAME, 'section')[1:]
            for section in sections:
                protocol_element = section.find_element(By.TAG_NAME, "h2")
                protocol, value = protocol_element.text.strip().replace('$', '').split()

                type = "Lending Borrowing"

                data = {
                    "Protocol": protocol,
                    "DeFi Type": type,
                    "Value": float(value)
                }
                
                data_list.append(data)

        except Exception as e:
            print(f"Erreur lors de la récupération des projets : {e}")
            
        return data_list

    def getProjectValueNotAccurate(self, project: WebElement):
        return project.find_element(By.CSS_SELECTOR, ".projectTitle-number").text.replace("$", "")

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
        scraping = ScrapSuiVision(wallet_address, "test", "0")
        
        holding_data = scraping.getHoldingsData()
        print(holding_data)
        holdAssets = scraping.getHoldAssets(holding_data)
        assets_list.extend(holdAssets)

        data_list = scraping.getDeFiPositionsData()
        print(data_list)
        defiAssets = scraping.getDeFiAssets(data_list)
        assets_list.extend(defiAssets)
        
        scraping.kill()
        
        print(f"Total assets to insert: {len(assets_list)}")
