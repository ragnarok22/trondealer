"""Check live balances for a TronDealer wallet."""

from __future__ import annotations

import os

from trondealer import TronDealerClient

client = TronDealerClient(api_key=os.environ["TRONDEALER_API_KEY"])
balance = client.get_wallet_balance(address="0xABCDEFabcdefABCDEFabcdefABCDEFabcdefABCD")

print(balance.model_dump(mode="json"))
