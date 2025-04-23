from RequestBankAccount import RequestBankAccount
from ScrapDebank import ScrapDebank
from datetime import datetime
from InteractSQL import InteractSQL
from wallets import wallets_evm
from datetime import timedelta
from Asset import Asset

def insert_asset(asset, db: InteractSQL):
    fields = list(asset.__dict__.keys())
    placeholders = ", ".join(["?" for _ in fields])
    columns = ", ".join(fields)

    values = tuple(getattr(asset, field) for field in fields)

    query = f"INSERT INTO assets ({columns}) VALUES ({placeholders})"
    db.execute_query(query, values)

sql = InteractSQL('DatabaseV1.db')
sql.connect()

assets_list = []
        
current_time = datetime.now()
rounded_time = current_time.replace(minute = 0, second = 0, microsecond = 0)
timestamp = rounded_time.strftime("%Y-%m-%d %H")
hour = int(timestamp[-2:])

do_sql_fallback = True
#Assets From Banks
if hour % 6 == 0:
    try:
        #On le fait que 4 fois par jour comme ça (limitation)
        hourlyRequestBank = RequestBankAccount(timestamp)
        accounts_list = hourlyRequestBank.get_accounts()
        balances = hourlyRequestBank.get_balances(accounts_list)
        assets_list.extend(hourlyRequestBank.get_assets(balances))
        do_sql_fallback = False
    except Exception as e:
        print(f"Problem : {e}")

if do_sql_fallback:
    # S'exécute si l'heure n'est pas un multiple de 6 ou s'il y a un problème
    # Calcul du timestamp de l'heure précédente
    prev_time = rounded_time - timedelta(hours=1)
    timestamp_prev_hour = prev_time.strftime("%Y-%m-%d %H")

    query = """
        SELECT amount FROM assets
        WHERE source = ? AND timestamp = ?
    """
    amounts_list = sql.fetch_all(query, ('Belfius', timestamp_prev_hour))

    # Extraire les montants depuis la liste de tuples
    amounts = [str(amount[0]) for amount in amounts_list]  # Accède à la première valeur de chaque tuple

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
    
    print(f"Total assets to insert: {len(assets_list)}")

for asset in assets_list:
    insert_asset(asset, sql)