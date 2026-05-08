"""Assign one TronDealer wallet per order or customer."""

from __future__ import annotations

import os

from trondealer import TronDealerClient

with TronDealerClient(api_key=os.environ["TRONDEALER_API_KEY"]) as client:
    wallet = client.assign_wallet(label="order-A-1024")

print(wallet.address)
