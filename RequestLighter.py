import asyncio
from datetime import datetime
from Asset import Asset
from AssetType import AssetType
from AssetSource import AssetSource
from FetchExchangeRates import FetchExchangeRates
import lighter


class RequestLighter:
    def __init__(
        self,
        wallet: str,
        wallet_name: str,
        timestamp: datetime,
        rates: FetchExchangeRates,
    ):
        self.wallet = wallet
        self.wallet_name = wallet_name
        self.timestamp = timestamp

        self.btc_eur = rates.getBtcEur()
        self.btc_usd = rates.getBtcUsd()
        self.usd_eur = rates.getUsdEur()

    async def _getEquity(self):
        client = lighter.ApiClient(
            configuration=lighter.Configuration(
                host="https://mainnet.zklighter.elliot.ai"
            )
        )
        try:
            account_api = lighter.AccountApi(client)
            try:
                acc = await account_api.account(by="l1_address", value=self.wallet)
                return float(acc.accounts[0].total_asset_value)
            except lighter.exceptions.BadRequestException as e:
                if "account not found" in str(e):
                    print(f"⚠️ Lighter: compte non trouvé pour {self.wallet}")
                    return 0.0
                else:
                    raise e  # On relance si c’est une autre erreur
        finally:
            await client.close()

    def getHoldAssets(self):
        # Récupère equity via asyncio
        equity = asyncio.run(self._getEquity())
        print(equity)
        # Lighter = equity en USDC uniquement
        asset = Asset(
            "Lighter total equity",
            AssetType.TRADING,
            AssetSource.LIGHTER,
            self.timestamp,
            "USD",
            self.usd_eur,
            self.btc_eur,
            self.btc_usd,
            value=float(equity),
            wallet_name=self.wallet_name,
        )

        return [asset]


if __name__ == "__main__":
    from datetime import datetime
    from FetchExchangeRates import FetchExchangeRates

    wallet = "0x9c7AaA2876517920041769f0D385f8cBb8893086"
    wallet_name = "test"
    timestamp = datetime.now()
    rates = FetchExchangeRates()

    request = RequestLighter(wallet, wallet_name, timestamp, rates)
    assets = request.getHoldAssets()

    for asset in assets:
        print(asset.value)
