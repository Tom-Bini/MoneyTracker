from selenium import webdriver
import time

# Configuration du navigateur (Chrome ici)
options = webdriver.ChromeOptions()
# Aucun headless, aucun stealth
driver = webdriver.Chrome(options=options)

# Ouvre la page
driver.get("https://portfolio.jup.ag/portfolio/9tfHcDsAPgZeAjWCwzC3aqY1C8NdfscDi5qAESt9vNNZ")

# Attend 1000 secondes
time.sleep(1000)

# Ferme le navigateur après (optionnel)
driver.quit()