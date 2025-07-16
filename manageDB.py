import sqlite3

# === CONFIGURATION ===
timestamp_a_supprimer = "2025-06-10 23"
nom_table = "assets"

# Connexion à la base de données
conn = sqlite3.connect("DatabaseV1.db")
cursor = conn.cursor()

# Requête de suppression
query = f"DELETE FROM {nom_table} WHERE timestamp = ?"
cursor.execute(query, (timestamp_a_supprimer,))
conn.commit()

# Résultat
print(f"{cursor.rowcount} lignes supprimées pour l'heure {timestamp_a_supprimer}.")

# Fermeture
conn.close()
