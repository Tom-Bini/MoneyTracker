from datetime import datetime
from AssetType import AssetType
from AssetSource import AssetSource


class Asset:  # Classe instancié chaque heure, qui gardera donc la valeur en €, $ et BTC historique
    def __init__(
        self,
        name: str,
        type: AssetType,
        source: AssetSource,
        timestamp: datetime,
        currency_exprimed: str,
        usd_eur: float,
        btc_eur: float,
        btc_usd: float,
        amount: float = None,
        price: float = None,
        value: float = None,
        ticker: str = None,
        isin: str = None,
        wallet_name: str = None,
        defi_type: str = None,
    ):
        self.name = name
        self.type = type.value
        self.source = source.value
        self.timestamp = timestamp
        self.amount = amount

        # btc_eur = nombre d'€ que vaut un btc (ex. 70k)
        # btc_usd = nombre d'$ que vaut un BTC (ex. 80k)
        # usd_eur = nombre d'€ que vaut un $ (ex. 0.89)
        currency_exprimed = currency_exprimed.upper().strip()
        if price != None:
            if currency_exprimed == "EUR":
                self.price_in_EUR = price
                self.price_in_USD = price / usd_eur
                self.price_in_BTC = price / btc_eur
            elif currency_exprimed == "USD":
                self.price_in_EUR = price * usd_eur
                self.price_in_USD = price
                self.price_in_BTC = price / btc_usd
            elif currency_exprimed == "BTC":
                self.price_in_EUR = price * btc_eur
                self.price_in_USD = price * btc_usd
                self.price_in_BTC = price
            else:
                raise ValueError(
                    f"{currency_exprimed} n'est pas une devise prise en charge pour l'Asset"
                )
        else:
            self.price_in_EUR = None
            self.price_in_USD = None
            self.price_in_BTC = None

        if value == None and amount != None:
            self.value_in_EUR = self.price_in_EUR * amount
            self.value_in_USD = self.price_in_USD * amount
            self.value_in_BTC = self.price_in_BTC * amount
        elif value != None:
            if currency_exprimed == "EUR":
                self.value_in_EUR = value
                self.value_in_USD = value / usd_eur
                self.value_in_BTC = value / btc_eur
            elif currency_exprimed == "USD":
                self.value_in_EUR = value * usd_eur
                self.value_in_USD = value
                self.value_in_BTC = value / btc_usd
            elif currency_exprimed == "BTC":
                self.value_in_EUR = value * btc_eur
                self.value_in_USD = value * btc_usd
                self.value_in_BTC = value
            else:
                raise ValueError(
                    f"{currency_exprimed} n'est pas une devise prise en charge pour l'Asset"
                )

        else:
            raise ValueError("Value et amount nuls, on peut rien faire mdr")

        if ticker != None:
            self.ticker = ticker
        if isin != None:
            self.isin = isin
        if wallet_name != None:
            self.wallet_name = wallet_name
        if defi_type != None:
            self.defi_type = defi_type
