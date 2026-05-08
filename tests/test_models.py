from __future__ import annotations

from trondealer.models import ClientRegistrationRequest, TransactionListResponse, WalletBalance
from trondealer.types import PayoutMethod


def test_wallet_balance_accepts_guide_network_shape_and_extra_fields() -> None:
    balance = WalletBalance.model_validate(
        {
            "success": True,
            "balances": {
                "bsc": {"native": "0.012", "usdt": "50.0", "usdc": "0.0"},
                "eth": {"native": "0.0", "usdt": "0.0", "usdc": "25.5"},
            },
            "new_field": "kept",
        }
    )

    assert balance.balances.root["bsc"].usdt == "50.0"
    assert balance.model_extra == {"new_field": "kept"}


def test_wallet_balance_accepts_openapi_flat_shape() -> None:
    balance = WalletBalance.model_validate(
        {"success": True, "balances": {"NativeToken": "0.1", "USDT": "1.0", "USDC": "2.0"}}
    )

    assert balance.balances.root["USDT"] == "1.0"


def test_transaction_list_allows_new_transaction_fields() -> None:
    response = TransactionListResponse.model_validate(
        {
            "success": True,
            "transactions": [
                {
                    "tx_hash": "0xabc",
                    "asset": "USDT",
                    "amount": "10.00",
                    "status": "confirmed",
                    "network": "bsc",
                    "webhook_sent": True,
                    "future_field": "value",
                }
            ],
        }
    )

    transaction = response.transactions[0]
    assert transaction.tx_hash == "0xabc"
    assert transaction.model_extra == {"future_field": "value"}


def test_default_collections_are_not_shared_between_models() -> None:
    first_balance = WalletBalance.model_validate({"success": True})
    second_balance = WalletBalance.model_validate({"success": True})
    first_balance.balances.root["bsc"] = "1.0"

    assert second_balance.balances.root == {}

    first_transactions = TransactionListResponse.model_validate({"success": True})
    second_transactions = TransactionListResponse.model_validate({"success": True})
    first_transactions.transactions.append({"tx_hash": "0xabc"})

    assert second_transactions.transactions == []


def test_registration_request_accepts_payout_method_enum_and_excludes_none() -> None:
    request = ClientRegistrationRequest(name="Shop", payout_method=PayoutMethod.WALLET)

    assert request.model_dump(mode="json", exclude_none=True) == {
        "name": "Shop",
        "payout_method": "wallet",
    }
