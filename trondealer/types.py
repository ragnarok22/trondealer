"""Shared public types for the TronDealer SDK."""

from __future__ import annotations

from enum import Enum


class StrEnum(str, Enum):
    """String enum with values that serialize naturally in JSON payloads."""

    def __str__(self) -> str:
        return self.value


class Network(StrEnum):
    BSC = "bsc"
    ETHEREUM = "eth"
    POLYGON = "pol"
    ARBITRUM = "arb"
    BASE = "base"
    OPTIMISM = "opt"
    AVALANCHE = "avax"
    TRON = "tron"
    SOLANA = "solana"


class Asset(StrEnum):
    USDT = "USDT"
    USDC = "USDC"


class TransactionStatus(StrEnum):
    DETECTED = "detected"
    CONFIRMED = "confirmed"
    NOTIFIED = "notified"
    SWEPT = "swept"


class PayoutMethod(StrEnum):
    WALLET = "wallet"
    QVAPAY = "qvapay"
    ZELLE = "zelle"


class WalletStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
