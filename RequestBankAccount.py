import os
import requests
from dotenv import load_dotenv
from dotenv import set_key
import json
from Asset import Asset
from AssetType import AssetType
from AssetSource import AssetSource
from datetime import datetime
from FetchExchangeRates import FetchExchangeRates

class RequestBankAccount:
    def __init__(self, timestamp, rates: FetchExchangeRates):
        # Charger les clés depuis le fichier .env
        load_dotenv()
        self.SECRET_ID = os.getenv("GOCARDLESS_SECRET_ID")
        self.SECRET_KEY = os.getenv("GOCARDLESS_SECRET_KEY")
        self.ACCESS_TOKEN = os.getenv("GOCARDLESS_ACCESS_TOKEN")
        self.REFRESH_TOKEN = os.getenv("GOCARDLESS_REFRESH_TOKEN")
        self.BANK_ID = os.getenv("GOCARDLESS_BANK_ID")
        self.REQUISITION_ID = os.getenv("GOCARDLESS_REQUISITION_ID")
        
        self.btc_eur = rates.getBtcEur()
        self.btc_usd = rates.getBtcUsd()
        self.usd_eur = rates.getUsdEur()
        
        self.timestamp = timestamp

    def get_tokens(self):
        # URL pour obtenir les tokens
        url = "https://bankaccountdata.gocardless.com/api/v2/token/new/"
        
        # Prépare le payload avec secret_id et secret_key
        payload = {
            "secret_id": self.SECRET_ID,
            "secret_key": self.SECRET_KEY
        }

        # En-têtes HTTP requis
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }

        # Envoie la requête POST pour récupérer les tokens
        response = requests.post(url, headers=headers, json=payload)
        
        # Vérifie si la requête a réussi
        if response.status_code != 200:
            print(f"Erreur {response.status_code} : {response.text}")
            response.raise_for_status()
        
        # Si la réponse est OK, récupère les tokens
        data = response.json()
        new_access_token = data["access"]
        new_refresh_token = data["refresh"]
        set_key(".env", "GOCARDLESS_ACCESS_TOKEN", new_access_token)
        set_key(".env", "GOCARDLESS_REFRESH_TOKEN", new_refresh_token)
        

    def refresh_token(self):
        url = "https://bankaccountdata.gocardless.com/api/v2/token/refresh/"
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json',
        }
        data = {
            "refresh": self.REFRESH_TOKEN
        }
        new_access_token = requests.post(url, headers=headers, json=data).json()["access"]
        set_key(".env", "GOCARDLESS_ACCESS_TOKEN", new_access_token)


    # Étape 2 – Récupérer les comptes bancaires
    def get_accounts(self):
        url = "https://bankaccountdata.gocardless.com/api/v2/requisitions/8126e9fb-93c9-4228-937c-68f0383c2df7/"
        headers = {
            "Authorization": f"Bearer {self.ACCESS_TOKEN}"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    def create_link(self):
        url = "https://bankaccountdata.gocardless.com/api/v2/requisitions/"

        data = {
        "redirect": "http://www.yourwebpage.com",
        "institution_id": self.BANK_ID
        }

        headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {self.ACCESS_TOKEN}"
        }

        response = requests.post(url, headers=headers, data=json.dumps(data))

        if response.status_code == 201:
            print("Réquisition créée avec succès")
            print(response.json())  # Afficher la réponse JSON
        else:
            print("Erreur lors de la création de la réquisition")
            print(response.status_code, response.text)

    def get_accounts(self):
        url = f"https://bankaccountdata.gocardless.com/api/v2/requisitions/{self.REQUISITION_ID}/"
        headers = {
            'accept': 'application/json',
            "Authorization": f"Bearer {self.ACCESS_TOKEN}"
        }
        response = requests.get(url, headers = headers).json()
        print(response)
        return response["accounts"]

    def get_account_details(self, account):
        url = f"https://bankaccountdata.gocardless.com/api/v2/accounts/{account}/details/"
        headers = {
            'accept': 'application/json',
            "Authorization": f"Bearer {self.ACCESS_TOKEN}"
        }
        print(requests.get(url, headers = headers).json())

    def get_balances(self, accounts_list):
        balances_list = []
        for account in accounts_list:
            url = f"https://bankaccountdata.gocardless.com/api/v2/accounts/{account}/balances/"
            headers = {
            'accept': 'application/json',
            "Authorization": f"Bearer {self.ACCESS_TOKEN}"
            }
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                balance = response.json()["balances"][0]["balanceAmount"]["amount"]
                balances_list.append(balance)
            else:
                print("Error :", response.status_code)

        return balances_list

    def get_bank_id(self, country = "be", bic = "GKCCBEBB"):
        url = f"https://bankaccountdata.gocardless.com/api/v2/institutions/?country={country}"
        headers = {
            'accept': 'application/json',
            "Authorization": f"Bearer {self.ACCESS_TOKEN}"
        }

        bank_list = requests.get(url, headers=headers).json()

        for bank in bank_list:
            if bank['bic'] == bic:
                print(f"Bank ID trouvé : {bank['id']}")
                return bank["id"]
        print("Combinaison country + Bic non géré ou mauvais")
        return 'false'
    
    def get_assets(self, amounts):
        assets_list = []
        for amount in amounts:
            amount = float(amount.replace(',', ''))
            assets_list.append(Asset("Euro", AssetType.FIAT, AssetSource.BELFIUS, self.timestamp, "EUR", self.usd_eur, self.btc_eur, self.btc_usd, amount, 1.0))
        return assets_list


if __name__ == "__main__":

    current_time = datetime.now()
    rounded_time = current_time.replace(minute = 0, second = 0, microsecond = 0)
    timestamp = rounded_time.strftime("%Y-%m-%d %H")

    hourlyRequestBank = RequestBankAccount(timestamp)
    
    accounts_list = hourlyRequestBank.get_accounts()
    print(accounts_list)
    balances = hourlyRequestBank.get_balances(accounts_list)
    print(balances)
    assets = hourlyRequestBank.get_assets(balances)
    print(assets)
    
