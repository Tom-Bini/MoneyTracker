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
import json
from typing import Dict, Union
from datetime import datetime
import yfinance as yf
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

class ScrapDebank:
    def __init__(self, wallet: str, wallet_name: str, timestamp: str):
        self.wallet = wallet
        self.wallet_name = wallet_name
        self.timestamp = timestamp
        self.usd_eur = yf.Ticker("USDEUR=X").history(period="1d")["Close"].iloc[-1]
        self.btc_eur = yf.Ticker("BTC-EUR").history(period="1d")["Close"].iloc[-1]
        self.btc_usd = yf.Ticker("BTC-USD").history(period="1d")["Close"].iloc[-1]
        
        options = Options()
        options.add_argument('--headless')  # Pour mode headless
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        # Initialiser le driver Selenium pour Firefox
        self.driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)

        # URL de la page DeBank
        self.url = f"https://debank.com/profile/{wallet}"
        
        # Ouvrir la page
        self.driver.get(self.url)

        # Attendre que la page se charge (peut être ajusté selon la vitesse de la connexion)
        time.sleep(20)

        # Dictionnaire pour stocker les données fusionnées par ticker
        self.hold_data = {}
        self.defi_data = {}

    def getHoldingsData(self):
        hold_data = {}
        try:
            # Trouver toutes les lignes du tableau
            rows = self.driver.find_elements(By.CSS_SELECTOR, ".db-table-row")

            for row in rows:
                try:
                    ticker = row.find_element(By.CSS_SELECTOR, ".db-table-cell:nth-child(1)").text
                    price = row.find_element(By.CSS_SELECTOR, ".db-table-cell:nth-child(2)").text
                    amount = row.find_element(By.CSS_SELECTOR, ".db-table-cell:nth-child(3)").text
                    
                    # Nettoyer les données (enlever le symbole '$' et les virgules)
                    price = safe_float_convert(price.replace('$', '').replace(',', '').strip())
                    amount = safe_float_convert(amount.replace(',', '').strip())
                    
                    # Si le ticker existe déjà, additionner les montants
                    if price == 0:
                        continue
                    elif ticker in hold_data:
                        hold_data[ticker]['amount'] += amount
                        # Le prix peut être mis à jour avec le dernier trouvé
                        hold_data[ticker]['price'] = price
                    else:
                        # Ajouter une nouvelle entrée pour ce ticker
                        hold_data[ticker] = {
                            "ticker": ticker,
                            "price": price,
                            "amount": amount
                        }

                except Exception as e:
                    print(f"Erreur lors de l'extraction d'une ligne : {e}")
            
        except Exception as e:
            print(f"Erreur lors de la récupération des données du tableau : {e}")

        return hold_data
        
    def getDeFiPositionsData(self):
        data_list = []

        try:
            projects = self.driver.find_elements(By.CSS_SELECTOR, ".Project_project__GCrhx")
            for project in projects:
                protocol = project.find_element(By.CSS_SELECTOR, ".ProjectTitle_protocolLink__4Yqn3").text
                type = project.find_element(By.CSS_SELECTOR, ".BookMark_bookmark__UG5a4").text
                value = self.getProjectValueNotAccurate(project)            
                if type == 'Lending':
                    type = 'Lending-Borrowing'
                elif type == 'Liquidity Pool' or type == 'Farming' or type == 'Yield':
                    type = 'Liquidity Providing'
                elif type == 'Staked':
                    type = 'Staking'

                data = {
                    "Protocol": protocol,
                    "DeFi Type": type,
                    "Value": value
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
            assets_list.append(Asset(data["Protocol"], AssetType.DEFI, AssetSource.EVM, self.timestamp, "USD", self.usd_eur, self.btc_eur, self.btc_usd, value = float(data["Value"]), wallet_name = self.wallet_name, defi_type = data["DeFi Type"]))
        return assets_list
        
    def kill(self):
        # Fermer le navigateur
        self.driver.quit()
