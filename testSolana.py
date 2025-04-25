from seleniumbase import SB
from selenium.webdriver.common.by import By
import time

with SB(uc=True, test=True, headless=False) as sb:
    url = "https://portfolio.jup.ag/portfolio/DHmzvbLXE9HJWjS1P2SVAjTNV32sp4xWRMtbmn3TWFCi"
    sb.open(url)  # Utilisation de open() au lieu de uc_open_with_reconnect
    print("Titre de la page:", sb.get_page_title())
    time.sleep(5)
    # Capture d'écran avant tentative de CAPTCHA
    sb.save_screenshot("before_captcha.png")
    
    # Attendre que le iframe de Cloudflare soit présent
    print("Recherche du CAPTCHA...")
    try:
        # Attendre et localiser l'iframe du CAPTCHA
        iframe = sb.wait_for_element_present("iframe[src*='challenges.cloudflare.com']", timeout=10)
        if iframe:
            print("CAPTCHA iframe trouvé, tentative de résolution...")
            # Passer au iframe
            sb.switch_to_frame(iframe)
            
            # Attendre et cliquer sur la case à cocher
            checkbox = sb.wait_for_element_present("input[type='checkbox']", timeout=5)
            if checkbox:
                sb.js_click(checkbox)  # Utiliser js_click pour plus de fiabilité
                print("Clic sur la case à cocher du CAPTCHA")
            else:
                # Si pas de checkbox standard, essayer le conteneur de la case
                checkbox_container = sb.wait_for_element_present(".captcha-checkbox", timeout=5)
                if checkbox_container:
                    sb.js_click(checkbox_container)
                    print("Clic sur le conteneur du CAPTCHA")
                
            # Revenir au contenu principal
            sb.switch_to_default_content()
    except Exception as e:
        print(f"Exception lors de la résolution du CAPTCHA: {e}")
        # Essayer la méthode générique de SeleniumBase
        try:
            sb.uc_gui_click_captcha()
            print("Tentative de clic générique sur le CAPTCHA")
        except Exception as e2:
            print(f"Exception lors du clic générique: {e2}")
    
    # Attendre le chargement de la page après CAPTCHA
    print("Attente du chargement de la page après CAPTCHA...")
    sb.wait_for_element_present(".portfolio-header, .portfolio-container", timeout=20)
    
    # Attente supplémentaire pour s'assurer du chargement complet
    time.sleep(5)
    
    # Capture d'écran finale
    sb.save_screenshot("after_captcha.png")
    
    print("Navigation terminée")