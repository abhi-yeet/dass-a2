"""Wallet, loyalty, and order endpoint tests."""

from __future__ import annotations

from typing import Any

import requests


def _extract_orders(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("orders", "data", "result", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def test_wallet_get_and_add_money_boundaries(
    session: requests.Session,
    base_url: str,
    user_headers: dict[str, str],
    timeout_seconds: float,
) -> None:
    get_wallet = session.get(
        f"{base_url}/api/v1/wallet",
        headers=user_headers,
        timeout=timeout_seconds,
    )
    assert get_wallet.status_code == 200

    too_low = session.post(
        f"{base_url}/api/v1/wallet/add",
        headers=user_headers,
        json={"amount": 0},
        timeout=timeout_seconds,
    )
    assert too_low.status_code == 400

    too_high = session.post(
        f"{base_url}/api/v1/wallet/add",
        headers=user_headers,
        json={"amount": 100001},
        timeout=timeout_seconds,
    )
    assert too_high.status_code == 400

    valid = session.post(
        f"{base_url}/api/v1/wallet/add",
        headers=user_headers,
        json={"amount": 100},
        timeout=timeout_seconds,
    )
    assert valid.status_code in (200, 201)


def test_wallet_add_wrong_type_rejected(
    session: requests.Session,
    base_url: str,
    user_headers: dict[str, str],
    timeout_seconds: float,
) -> None:
    response = session.post(
        f"{base_url}/api/v1/wallet/add",
        headers=user_headers,
        json={"amount": "one hundred"},
        timeout=timeout_seconds,
    )
    assert response.status_code == 400


def test_wallet_pay_invalid_amount_and_insufficient_balance(
    session: requests.Session,
    base_url: str,
    user_headers: dict[str, str],
    timeout_seconds: float,
) -> None:
    invalid = session.post(
        f"{base_url}/api/v1/wallet/pay",
        headers=user_headers,
        json={"amount": 0},
        timeout=timeout_seconds,
    )
    assert invalid.status_code == 400

    huge = session.post(
        f"{base_url}/api/v1/wallet/pay",
        headers=user_headers,
        json={"amount": 99999999},
        timeout=timeout_seconds,
    )
    assert huge.status_code == 400


def test_loyalty_get_and_redeem_invalid(
    session: requests.Session,
    base_url: str,
    user_headers: dict[str, str],
    timeout_seconds: float,
) -> None:
    get_loyalty = session.get(
        f"{base_url}/api/v1/loyalty",
        headers=user_headers,
        timeout=timeout_seconds,
    )
    assert get_loyalty.status_code == 200

    redeem_zero = session.post(
        f"{base_url}/api/v1/loyalty/redeem",
        headers=user_headers,
        json={"points": 0},
        timeout=timeout_seconds,
    )
    assert redeem_zero.status_code == 400


def test_orders_and_nonexistent_order(
    session: requests.Session,
    base_url: str,
    user_headers: dict[str, str],
    timeout_seconds: float,
) -> None:
    orders = session.get(
        f"{base_url}/api/v1/orders",
        headers=user_headers,
        timeout=timeout_seconds,
    )
    assert orders.status_code == 200
    order_list = _extract_orders(orders.json())
    assert isinstance(order_list, list)

    missing = session.get(
        f"{base_url}/api/v1/orders/9999999",
        headers=user_headers,
        timeout=timeout_seconds,
    )
    assert missing.status_code == 404

    invoice_missing = session.get(
        f"{base_url}/api/v1/orders/9999999/invoice",
        headers=user_headers,
        timeout=timeout_seconds,
    )
    assert invoice_missing.status_code == 404
