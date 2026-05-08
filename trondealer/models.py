"""Pydantic models for documented TronDealer API payloads."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, RootModel, model_validator

from .types import Asset, Network, PayoutMethod, TransactionStatus, WalletStatus


class SDKModel(BaseModel):
    """Base model that tolerates new response fields added by the API."""

    model_config = ConfigDict(extra="allow", use_enum_values=True)


class ClientRegistrationRequest(SDKModel):
    name: str
    webhook_url: str | None = None
    webhook_secret: str | None = None
    min_confirmations: int | None = None
    sweep_wallet: str | None = None
    payout_method: PayoutMethod | None = None
    turnstile_token: str | None = None


class Client(SDKModel):
    id: str | None = None
    name: str | None = None
    api_key: str | None = None
    webhook_url: str | None = None
    min_confirmations: int | None = None
    sweep_wallet: str | None = None
    sweep_wallet_evm: str | None = None
    sweep_wallet_tron: str | None = None
    payout_method: PayoutMethod | None = None
    qvapay_account: str | None = None
    zelle_contact: str | None = None
    is_active: bool | None = None
    created_at: datetime | None = None


class ClientRegistrationResponse(SDKModel):
    success: bool | None = None
    client: Client


class AssignedWallet(SDKModel):
    id: str | None = None
    address: str
    label: str | None = None
    status: WalletStatus | str | None = None
    created_at: datetime | None = None


class AssignedWalletResponse(SDKModel):
    success: bool | None = None
    wallet: AssignedWallet


class NetworkBalance(SDKModel):
    native: str | None = None
    usdt: str | None = None
    usdc: str | None = None
    NativeToken: str | None = None
    USDT: str | None = None
    USDC: str | None = None


class WalletInfo(SDKModel):
    address: str | None = None
    label: str | None = None
    status: WalletStatus | str | None = None


class BalanceMap(RootModel[dict[str, NetworkBalance | str]]):
    """Flexible balance map for guide and OpenAPI response variants."""


class WalletBalance(SDKModel):
    success: bool | None = None
    wallet: WalletInfo | None = None
    balances: BalanceMap = Field(default_factory=lambda: BalanceMap({}))


class Transaction(SDKModel):
    tx_hash: str | None = None
    tx_id: str | None = None
    tx_signature: str | None = None
    log_index: int | None = None
    event_index: int | None = None
    instruction_index: int | None = None
    block_number: int | None = None
    slot: int | None = None
    from_address: str | None = None
    to_address: str | None = None
    asset: Asset | str | None = None
    amount: str | None = None
    amount_raw: str | None = None
    confirmations: int | None = None
    status: TransactionStatus | str | None = None
    network: Network | str | None = None
    webhook_sent: bool | None = None
    detected_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TransactionListResponse(SDKModel):
    success: bool | None = None
    wallet: WalletInfo | None = None
    total: int | None = None
    limit: int | None = None
    offset: int | None = None
    transactions: list[Transaction] = Field(default_factory=list)


class WebhookTransactionData(SDKModel):
    tx_hash: str | None = None
    log_index: int | None = None
    event_index: int | None = None
    instruction_index: int | None = None
    block_number: int | None = None
    from_address: str | None = None
    to_address: str | None = None
    asset: Asset | str | None = None
    amount: str | None = None
    confirmations: int | None = None
    wallet_label: str | None = None
    network: Network | str | None = None


class WebhookSweptData(SDKModel):
    sweep_tx_hash: str | None = None
    fee_tx_hash: str | None = None
    funding_tx_hash: str | None = None
    source_tx_hashes: list[str] = Field(default_factory=list)
    asset: Asset | str | None = None
    amount: str | None = None
    gross_amount: str | None = None
    fee_amount: str | None = None
    destination: str | None = None
    wallet_address: str | None = None
    wallet_label: str | None = None
    network: Network | str | None = None


WebhookData = dict[str, Any] | WebhookTransactionData | WebhookSweptData


class WebhookEvent(SDKModel):
    event: str
    timestamp: datetime | None = None
    data: WebhookData

    @model_validator(mode="after")
    def coerce_event_data(self) -> WebhookEvent:
        if isinstance(self.data, dict):
            if self.event == "transaction.swept":
                self.data = WebhookSweptData.model_validate(self.data)
            else:
                self.data = WebhookTransactionData.model_validate(self.data)
        return self
