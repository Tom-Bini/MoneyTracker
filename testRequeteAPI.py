import requests

def get_api_data(url, headers=None, params=None):
    """
    Effectue une requête GET avec des headers et des paramètres (payload).
    
    :param url: URL de l'API
    :param headers: dictionnaire des en-têtes HTTP
    :param params: dictionnaire des paramètres GET (payload)
    :return: réponse JSON ou None en cas d'erreur
    """
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Lève une exception pour les erreurs HTTP (ex: 404, 500)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la requête API: {e}")
        return None
