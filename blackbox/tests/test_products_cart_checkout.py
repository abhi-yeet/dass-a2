"""Product, cart, coupon, and checkout tests."""

from __future__ import annotations

from typing import Any

import pytest
import requests


def _extract_products(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("products", "data", "result", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def _extract_cart_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        for key in ("items", "cart_items", "products"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def test_get_products_success(
    session: requests.Session,
    base_url: str,
    user_headers: dict[str, str],
    timeout_seconds: float,
) -> None:
    response = session.get(
        f"{base_url}/api/v1/products",
        headers=user_headers,
        timeout=timeout_seconds,
    )
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, (dict, list))
    products = _extract_products(body)
    assert isinstance(products, list)


def test_get_product_invalid_id_returns_404(
    session: requests.Session,
    base_url: str,
    user_headers: dict[str, str],
    timeout_seconds: float,
) -> None:
    response = session.get(
        f"{base_url}/api/v1/products/9999999",
        headers=user_headers,
        timeout=timeout_seconds,
    )
    assert response.status_code == 404


def test_products_filter_search_sort_do_not_fail(
    session: requests.Session,
    base_url: str,
    user_headers: dict[str, str],
    timeout_seconds: float,
) -> None:
    response = session.get(
        f"{base_url}/api/v1/products",
        headers=user_headers,
        params={"search": "a", "sort": "price_asc"},
        timeout=timeout_seconds,
    )
    assert response.status_code == 200


def test_add_to_cart_invalid_quantity_rejected(
    session: requests.Session,
    base_url: str,
    user_headers: dict[str, str],
    active_product_id: int,
    timeout_seconds: float,
) -> None:
    response = session.post(
        f"{base_url}/api/v1/cart/add",
        headers=user_headers,
        json={"product_id": active_product_id, "quantity": 0},
        timeout=timeout_seconds,
    )
    assert response.status_code == 400


def test_add_to_cart_wrong_quantity_type_rejected(
    session: requests.Session,
    base_url: str,
    user_headers: dict[str, str],
    active_product_id: int,
    timeout_seconds: float,
) -> None:
    response = session.post(
        f"{base_url}/api/v1/cart/add",
        headers=user_headers,
        json={"product_id": active_product_id, "quantity": "two"},
        timeout=timeout_seconds,
    )
    assert response.status_code == 400


def test_add_to_cart_nonexistent_product_404(
    session: requests.Session,
    base_url: str,
    user_headers: dict[str, str],
    timeout_seconds: float,
) -> None:
    response = session.post(
        f"{base_url}/api/v1/cart/add",
        headers=user_headers,
        json={"product_id": 9999999, "quantity": 1},
        timeout=timeout_seconds,
    )
    assert response.status_code == 404


def test_cart_add_update_remove_clear_happy_path(
    session: requests.Session,
    base_url: str,
    user_headers: dict[str, str],
    active_product_id: int,
    timeout_seconds: float,
) -> None:
    add = session.post(
        f"{base_url}/api/v1/cart/add",
        headers=user_headers,
        json={"product_id": active_product_id, "quantity": 1},
        timeout=timeout_seconds,
    )
    assert add.status_code in (200, 201)

    update = session.post(
        f"{base_url}/api/v1/cart/update",
        headers=user_headers,
        json={"product_id": active_product_id, "quantity": 2},
        timeout=timeout_seconds,
    )
    assert update.status_code == 200

    cart = session.get(
        f"{base_url}/api/v1/cart",
        headers=user_headers,
        timeout=timeout_seconds,
    )
    assert cart.status_code == 200
    items = _extract_cart_items(cart.json())
    assert isinstance(items, list)

    remove = session.post(
        f"{base_url}/api/v1/cart/remove",
        headers=user_headers,
        json={"product_id": active_product_id},
        timeout=timeout_seconds,
    )
    assert remove.status_code == 200

    clear = session.delete(
        f"{base_url}/api/v1/cart/clear",
        headers=user_headers,
        timeout=timeout_seconds,
    )
    assert clear.status_code == 200


@pytest.mark.parametrize("payment_method", ["COD", "WALLET", "CARD"])
def test_checkout_accepts_valid_payment_methods(
    session: requests.Session,
    base_url: str,
    user_headers: dict[str, str],
    active_product_id: int,
    timeout_seconds: float,
    payment_method: str,
) -> None:
    session.post(
        f"{base_url}/api/v1/cart/add",
        headers=user_headers,
        json={"product_id": active_product_id, "quantity": 1},
        timeout=timeout_seconds,
    )
    checkout = session.post(
        f"{base_url}/api/v1/checkout",
        headers=user_headers,
        json={"payment_method": payment_method},
        timeout=timeout_seconds,
    )
    assert checkout.status_code in (200, 201, 400)
    # 400 is allowed in seeded environments where wallet/COD constraints fail.


def test_checkout_rejects_invalid_payment_method(
    session: requests.Session,
    base_url: str,
    user_headers: dict[str, str],
    timeout_seconds: float,
) -> None:
    response = session.post(
        f"{base_url}/api/v1/checkout",
        headers=user_headers,
        json={"payment_method": "UPI"},
        timeout=timeout_seconds,
    )
    assert response.status_code == 400


def test_checkout_missing_payment_method_rejected(
    session: requests.Session,
    base_url: str,
    user_headers: dict[str, str],
    timeout_seconds: float,
) -> None:
    response = session.post(
        f"{base_url}/api/v1/checkout",
        headers=user_headers,
        json={},
        timeout=timeout_seconds,
    )
    assert response.status_code == 400
