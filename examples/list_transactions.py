"""List confirmed wallet transactions."""

from __future__ import annotations

import os

from trondealer import TronDealerClient

client = TronDealerClient(api_key=os.environ["TRONDEALER_API_KEY"])
transactions = client.list_wallet_transactions(
    address="0xABCDEFabcdefABCDEFabcdefABCDEFabcdefABCD",
    status="confirmed",
    limit=20,
    offset=0,
)

for transaction in transactions.transactions:
    print(transaction.tx_hash, transaction.amount, transaction.status)
