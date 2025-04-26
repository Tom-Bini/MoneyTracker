from RequestBankAccount import RequestBankAccount
from ScrapDebank import ScrapDebank
from ScrapSuiVision import ScrapSuiVision
from RequestBitget import RequestBitget
from datetime import datetime
from InteractSQL import InteractSQL
from wallets import wallets_evm
from wallets import wallets_sui
from datetime import timedelta
from Asset import Asset

print("Début de l'exécution de HourlyAssets.py au timestamp : {}")

def insert_asset(asset, db: InteractSQL):
    fields = list(asset.__dict__.keys())
    placeholders = ", ".join(["?" for _ in fields])
    columns = ", ".join(fields)

    values = tuple(getattr(asset, field) for field in fields)

    query = f"INSERT INTO assets ({columns}) VALUES ({placeholders})"
    db.execute_query(query, values)
    
assets_list = []
        
current_time = datetime.now()
rounded_time = current_time.replace(minute = 0, second = 0, microsecond = 0)
timestamp = rounded_time.strftime("%Y-%m-%d %H")
hour = int(timestamp[-2:])

print(f"Début de l'exécution de HourlyAssets.py à : {current_time}")

sql = InteractSQL('DatabaseV1.db')
sql.connect()



do_sql_fallback = True
#Assets From Banks
if hour % 6 == 1:
    try:
        #On le fait que 4 fois par jour comme ça (limitation)
        hourlyRequestBank = RequestBankAccount(timestamp)
        if hour == 18:
            print("Refresh de l'access token quotidien")
            hourlyRequestBank.refresh_token() #On va reprendre un nouveau token Access
            hourlyRequestBank = RequestBankAccount(timestamp) #On réinitialise l'objet avec le nouvel access token
        accounts_list = hourlyRequestBank.get_accounts()
        balances = hourlyRequestBank.get_balances(accounts_list)
        if balances != []:
            do_sql_fallback = False
            assets_list.extend(hourlyRequestBank.get_assets(balances))
        
    except Exception as e:
        print(f"Problème dans la requête à la banque : {e}")

if do_sql_fallback:
    # S'exécute si l'heure n'est pas un multiple de 6 ou s'il y a un problème
    
    query = """
        SELECT amount FROM assets
        WHERE source = ?
        ORDER BY timestamp DESC
        LIMIT 1
    """
    amounts_list = sql.fetch_all(query, ('Belfius',))

    # Extraire les montants depuis la liste de tuples
    amounts = [str(amount[0]) for amount in amounts_list]  # Accède à la première valeur de chaque tuple
    print("Valeurs récupérées en dépit de :", amounts)

    # Passe la liste des montants extraits en argument à la fonction
    assets_list.extend(RequestBankAccount(timestamp).get_assets(amounts))
    
#Assets from EVM
for wallet_name in wallets_evm:
    wallet_address = wallets_evm[wallet_name]
    scraping = ScrapDebank(wallet_address, wallet_name, timestamp)
    
    holding_data = scraping.getHoldingsData()
    print(holding_data)
    holdAssets = scraping.getHoldAssets(holding_data)
    assets_list.extend(holdAssets)

    data_list = scraping.getDeFiPositionsData()
    print(data_list)
    defiAssets = scraping.getDeFiAssets(data_list)
    assets_list.extend(defiAssets)
    
    scraping.kill()
    
    print(f"Total assets to insert from EVM: {len(assets_list)}")
    
#Assets from SUI

for wallet_name in wallets_sui:
    wallet_address = wallets_sui[wallet_name]
    scraping = ScrapSuiVision(wallet_address, wallet_name, timestamp)
    
    holding_data = scraping.getHoldingsData()
    print(holding_data)
    holdAssets = scraping.getHoldAssets(holding_data)
    assets_list.extend(holdAssets)

    data_list = scraping.getDeFiPositionsData()
    print(data_list)
    defiAssets = scraping.getDeFiAssets(data_list)
    assets_list.extend(defiAssets)
    
    scraping.kill()
    
    print(f"Total assets to insert from SUI: {len(assets_list)}")
    
#Assets from Bitget

request = RequestBitget(timestamp)
bitget_data = request.fetch_assets_snapshot()
bitgetAssets = request.getHoldAssets(bitget_data)
assets_list.extend(bitgetAssets)

for asset in assets_list:
    insert_asset(asset, sql)
    
print(f"Insertion de {len(assets_list)} assets avec succès !")
print("fin de Hourly Assets")