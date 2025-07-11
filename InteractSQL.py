import sqlite3

class InteractSQL:
    def __init__(self, db_name: str):
        
        #Initialisation de la classe

        self.db_name = db_name
        self.conn = None
        self.cur = None

    def connect(self):

        #Connexion à la database

        self.conn = sqlite3.connect(self.db_name)
        self.cur = self.conn.cursor()

    def create_table(self, query: str):
        
        #Crée une table en fonction de la requête fournie

        if self.conn is None:
            raise Exception("Connexion non établie à la database")
        
        self.cur.execute(query)
        self.conn.commit()

    def execute_query(self, query: str, params = None):

        #Exécute une requête SQL avec ou sans paramètres
        if self.conn is None:
            raise Exception("Connexion non établie à la database")

        if params:
            self.cur.execute(query, params)

        else:
            self.cur.execute(query)

        self.conn.commit()

    def fetch_all(self, query, params = None):
        #Récupère toutes les lignes pour une requête Select
        if self.conn is None:
            raise Exception("Connexion non établie à la database")

        if params:
            self.cur.execute(query, params)

        else:
            self.cur.execute(query)

        return self.cur.fetchall()
    
    def close(self):
        #Ferme la connexion à la database
        if self.conn:
            self.conn.close()