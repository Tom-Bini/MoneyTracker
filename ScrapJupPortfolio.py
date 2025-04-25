#DECOMMENTER AVANT D'UPLOAD
from seleniumbase import SB
from selenium import webdriver
#from selenium.webdriver.firefox.options import Options  # Importer Options pour Firefox
from selenium.webdriver.common.by import By
#from selenium.webdriver.firefox.service import Service  # Service pour Firefox
#from webdriver_manager.firefox import GeckoDriverManager  # Utilisation de GeckoDriverManager pour Firefox
from selenium.webdriver.remote.webelement import WebElement
from Asset import Asset
from AssetType import AssetType
from AssetSource import AssetSource
import time
import os
from typing import Dict, Union
from datetime import datetime
import yfinance as yf
import re

#A RETIRER AVANT D'UPLOAD :

from selenium.webdriver.chrome.options import Options  # Remplace l'import Firefox par Chrome
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

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

class ScrapJupPortfolio:
    def __init__(self, wallet: str, wallet_name: str, timestamp: str, sb: SB):
        self.wallet = wallet
        self.wallet_name = wallet_name
        self.timestamp = timestamp
        self.usd_eur = yf.Ticker("USDEUR=X").history(period="1d")["Close"].iloc[-1]
        self.btc_eur = yf.Ticker("BTC-EUR").history(period="1d")["Close"].iloc[-1]
        self.btc_usd = yf.Ticker("BTC-USD").history(period="1d")["Close"].iloc[-1]

        self.url = f"https://portfolio.jup.ag/portfolio/{wallet}"
        print(f"Ouverture de l'URL: {self.url}")
        sb.uc_open_with_reconnect(self.url, 4)
        print(sb.get_page_title())
        sb.uc_gui_click_captcha()  # Only used if needed
        print(sb.get_page_title())

        print("Attente du chargement de la page...")
        time.sleep(15)

        self.hold_data = {}
        self.defi_data = {}
    
    def getHoldingsData(self, sb):
        hold_data = {}
        
        main = sb.find_element(By.TAG_NAME, 'main')
        print(main.get_attribute('outerHTML'))
        holding_details = main.find_element(By.TAG_NAME, 'details')
        rows = holding_details.find_elements(By.TAG_NAME, 'tr')[1:]
        for row in rows:
            ticker = row.find_element(By.TAG_NAME, 'button').text
            print(ticker)
            span_list = row.find_elements(By.TAG_NAME, 'span')[1:]
            amount = float(span_list[0].text.replace('$', ''))
            print(amount)
            price = float(span_list[1].text.replace('$', ''))
            print(price)
            value = span_list[2].text
            if value != "<$0.01":
                value = float(value.replace('$', ''))
                hold_data[ticker] = {
                    "ticker": ticker,
                    "price": price,
                    "amount": amount
                }
                
        return hold_data
        
    def getDeFiPositionsData(self, sb):
        data_list = []
        main = sb.find_element(By.TAG_NAME, 'main')
        defi_details = main.find_elements(By.TAG_NAME, 'details')[1:]
        for detail in defi_details:
            protocol = detail.find_element(By.TAG_NAME, 'p').text
            print(protocol)
            tabs = detail.find_elements(By.CSS_SELECTOR, '.rounded-jup.border.border-white\\/20.bg-surface')
            for tab in tabs:
                type = tab.find_element(By.TAG_NAME, 'span').text
                
                if type == 'Lending':
                    type = 'Lending-Borrowing'
                elif type == 'LiquidityPool':
                    type = 'Liquidity Providing'
                elif type == 'Staked' or type == 'Rewards':
                    type = 'Staking'
                print(type)
                if type == 'Liquidity Providing':
                    tr_list = tab.find_elements(By.TAG_NAME, 'tr')
                    raw_value = tr_list[1].find_elements(By.TAG_NAME, 'span')[-1].text
                    value = 0
                    if raw_value != '<$0.01':
                        value = float(raw_value.replace('$', ''))
                        print(value)
                    if len(tr_list) > 2:
                        reward = tr_list[3].find_elements(By.TAG_NAME, 'span')[-1].text
                        if reward != "<$0.01":
                            value += float(reward.replace('$', ''))
                elif type == 'Staking':
                    tr_list = tab.find_elements(By.TAG_NAME, 'tr')
                    raw_value = tr_list[1].find_elements(By.TAG_NAME, 'span')[-1].text
                    value = 0
                    if raw_value != '<$0.01':
                        value = raw_value.replace('$', '')
                        print(value)
                elif type == 'Lending-Borrowing':
                    tr_list = tab.find_elements(By.TAG_NAME, 'tr')
                    raw_supplied = tr_list[1].find_elements(By.TAG_NAME, 'span')[-1].text
                    value = 0
                    if raw_supplied != '<$0.01':
                        value = raw_supplied.replace('$', '')
                        print(value)
                    if len(tr_list) > 2:
                        borrowed = tr_list[3].find_elements(By.TAG_NAME, 'span')[-1].text
                        if borrowed != "<$0.01":
                            value -= float(borrowed.replace('$', '')) 
                
                
                data = {
                    "Protocol": protocol,
                    "DeFi Type": type,
                    "Value": value
                }
                
                if value != 0:
                    data_list.append(data)
            
        return data_list

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
    wallet_address = "DHmzvbLXE9HJWjS1P2SVAjTNV32sp4xWRMtbmn3TWFCi"
    with SB(uc=True, test=True) as sb:
        sb.driver.set_window_size(1920, 1080)
        scraping = ScrapJupPortfolio(wallet_address, "test", "0", sb)
        
        holdings = scraping.getHoldingsData(sb)
        hold_assets = scraping.getHoldAssets(holdings)
        assets_list.extend(hold_assets)
        
        defi = scraping.getDeFiPositionsData(sb)
        defi_assets = scraping.getDeFiAssets(defi)
        assets_list.extend(defi_assets)
        
        print(f"Total assets to insert: {len(assets_list)}")
        