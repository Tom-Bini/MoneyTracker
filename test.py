from InteractSQL import InteractSQL

sql = InteractSQL('DatabaseV1.db')
sql.connect()

sql.create_table("""
CREATE TABLE IF NOT EXISTS assets (
    name TEXT,
    type TEXT,
    source TEXT,
    timestamp TEXT,
    amount REAL,
    price_in_EUR REAL,
    price_in_USD REAL,
    price_in_BTC REAL,
    value_in_EUR REAL,
    value_in_USD REAL,
    value_in_BTC REAL,
    ticker TEXT,
    isin TEXT,
    wallet_name TEXT,
    defi_type TEXT
)
""")
