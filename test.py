import requests

address = "DHmzvbLXE9HJWjS1P2SVAjTNV32sp4xWRMtbmn3TWFCi"
url = f"https://portfolio-api-public.sonar.watch/api/v1/ping/"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123 Safari/537.36"
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    positions = response.json()
    for position in positions:
        print(position)
else:
    print(f"Erreur {response.status_code}")