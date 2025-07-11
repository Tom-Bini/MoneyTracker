from datetime import datetime
from datetime import timedelta
from InteractSQL import InteractSQL

sql = InteractSQL('DatabaseV1.db')
sql.connect()

current_time = datetime.now()
rounded_time = current_time.replace(minute = 0, second = 0, microsecond = 0)

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
print(amounts)