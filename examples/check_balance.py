"""Check live balances for a TronDealer wallet."""

from __future__ import annotations

import os

from trondealer import TronDealerClient

with TronDealerClient(api_key=os.environ["TRONDEALER_API_KEY"]) as client:
    balance = client.get_wallet_balance(address="0xABCDEFabcdefABCDEFabcdefABCDEFabcdefABCD")

print(balance.model_dump(mode="json"))
