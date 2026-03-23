"""Pytest configuration and shared fixtures for QuickCart black-box tests."""

from __future__ import annotations

import os
from typing import Any

import pytest
import requests


def _extract_users(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("users", "data", "result", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        return [payload]
    return []


def _extract_products(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("products", "data", "result", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


@pytest.fixture(scope="session")
def base_url() -> str:
    return os.getenv("QC_BASE_URL", "http://localhost:8080").rstrip("/")


@pytest.fixture(scope="session")
def roll_number() -> str:
    return os.getenv("QC_ROLL_NUMBER", "20260001")


@pytest.fixture(scope="session")
def timeout_seconds() -> float:
    return float(os.getenv("QC_TIMEOUT", "8"))


@pytest.fixture(scope="session", autouse=True)
def ensure_server_reachable(base_url: str, timeout_seconds: float) -> None:
    """Skip suite when API server is not running."""
    try:
        # 401 here is fine; it proves the server is reachable.
        requests.get(f"{base_url}/api/v1/admin/users", timeout=timeout_seconds)
    except requests.RequestException as exc:
        pytest.skip(
            f"QuickCart API is unreachable at {base_url}: {exc}",
            allow_module_level=True,
        )


@pytest.fixture(scope="session")
def session() -> requests.Session:
    return requests.Session()


@pytest.fixture(scope="session")
def admin_headers(roll_number: str) -> dict[str, str]:
    return {"X-Roll-Number": roll_number}


@pytest.fixture(scope="session")
def user_id(
    session: requests.Session,
    base_url: str,
    admin_headers: dict[str, str],
    timeout_seconds: float,
) -> int:
    response = session.get(
        f"{base_url}/api/v1/admin/users",
        headers=admin_headers,
        timeout=timeout_seconds,
    )
    if response.status_code != 200:
        pytest.skip(
            "Cannot derive a valid user_id because /admin/users did not return 200."
        )
    users = _extract_users(response.json())
    if not users:
        pytest.skip("No users available in seed data for user-scoped endpoint tests.")
    first = users[0]
    for key in ("user_id", "id"):
        value = first.get(key)
        if isinstance(value, int) and value > 0:
            return value
    pytest.skip("Could not find an integer user id field in /admin/users response.")


@pytest.fixture(scope="session")
def user_headers(admin_headers: dict[str, str], user_id: int) -> dict[str, str]:
    headers = dict(admin_headers)
    headers["X-User-ID"] = str(user_id)
    return headers


@pytest.fixture(scope="session")
def active_product_id(
    session: requests.Session,
    base_url: str,
    user_headers: dict[str, str],
    timeout_seconds: float,
) -> int:
    response = session.get(
        f"{base_url}/api/v1/products",
        headers=user_headers,
        timeout=timeout_seconds,
    )
    if response.status_code != 200:
        pytest.skip("Cannot derive a product id because /products did not return 200.")
    products = _extract_products(response.json())
    if not products:
        pytest.skip("No products available for cart/review integration tests.")
    product = products[0]
    for key in ("product_id", "id"):
        value = product.get(key)
        if isinstance(value, int) and value > 0:
            return value
    pytest.skip("Could not find an integer product id field in /products response.")

