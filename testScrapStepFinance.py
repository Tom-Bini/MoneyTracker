from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import json

def getDebankHoldingAmount(walletAddress):
    # Initialiser le driver Selenium
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    # URL de la page Step Finance (remplacer l'adresse du portefeuille)
    url = f"https://portfolio.jup.ag/portfolio/{walletAddress}"

    # Ouvrir la page
    driver.get(url)

    # Attendre que la page se charge (peut être ajusté selon la vitesse de la connexion)
    time.sleep(5)  # Attendre 5 secondes (à ajuster selon ton réseau)

    # Dictionnaire pour stocker les données par ticker
    assets_data = {}

    try:
        # Trouver toutes les lignes du tableau (chaque ligne représente un actif)
        rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr")

        for row in rows:
            try:
                # Récupérer le ticker (nom de la crypto, comme "SOL", "USDC")
                ticker = row.find_element(By.CSS_SELECTOR, "td:nth-child(1) span").text.strip()

                # Récupérer le montant
                amount = row.find_element(By.CSS_SELECTOR, "td:nth-child(6) span").text.strip()
                amount = float(amount.replace(',', ''))

                # Récupérer le prix en USD
                price = row.find_element(By.CSS_SELECTOR, "td:nth-child(4) span span").text.strip()
                price = float(price.replace('$', '').replace(',', ''))

                # Ajouter ou mettre à jour les informations dans le dictionnaire
                if ticker in assets_data:
                    assets_data[ticker]['amount'] += amount
                    assets_data[ticker]['price'] = price  # Met à jour le prix
                else:
                    assets_data[ticker] = {
                        "ticker": ticker,
                        "price": price,
                        "amount": amount
                    }

            except Exception as e:
                print(f"Erreur lors de l'extraction d'une ligne : {e}")

        # Convertir les données en format JSON
        assets_json = json.dumps(list(assets_data.values()), indent=4)
        print(assets_json)

    except Exception as e:
        print(f"Erreur lors de la récupération des données du tableau : {e}")

    # Fermer le navigateur
    driver.quit()

    return assets_json

# Exemple d'appel de la fonction avec une adresse de portefeuille
walletAddress = "DHmzvbLXE9HJWjS1P2SVAjTNV32sp4xWRMtbmn3TWFCi"
print(getDebankHoldingAmount(walletAddress))
