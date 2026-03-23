"""Header validation and admin endpoint smoke tests."""

from __future__ import annotations

from typing import Any

import pytest
import requests


def _is_json_like(payload: Any) -> bool:
    return isinstance(payload, (dict, list))


@pytest.mark.parametrize(
    ("headers", "expected_status"),
    [
        ({}, 401),  # Missing X-Roll-Number
        ({"X-Roll-Number": "abc"}, 400),  # Invalid integer
    ],
)
def test_roll_number_header_validation(
    session: requests.Session,
    base_url: str,
    timeout_seconds: float,
    headers: dict[str, str],
    expected_status: int,
) -> None:
    response = session.get(
        f"{base_url}/api/v1/admin/users",
        headers=headers,
        timeout=timeout_seconds,
    )
    assert response.status_code == expected_status


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/admin/users",
        "/api/v1/admin/carts",
        "/api/v1/admin/orders",
        "/api/v1/admin/products",
        "/api/v1/admin/coupons",
        "/api/v1/admin/tickets",
        "/api/v1/admin/addresses",
    ],
)
def test_admin_endpoints_return_json(
    session: requests.Session,
    base_url: str,
    admin_headers: dict[str, str],
    timeout_seconds: float,
    path: str,
) -> None:
    response = session.get(
        f"{base_url}{path}",
        headers=admin_headers,
        timeout=timeout_seconds,
    )
    assert response.status_code == 200
    assert _is_json_like(response.json())


def test_user_scoped_endpoint_requires_user_id(
    session: requests.Session,
    base_url: str,
    admin_headers: dict[str, str],
    timeout_seconds: float,
) -> None:
    response = session.get(
        f"{base_url}/api/v1/profile",
        headers=admin_headers,  # No X-User-ID
        timeout=timeout_seconds,
    )
    assert response.status_code == 400


@pytest.mark.parametrize("bad_user_id", ["abc", "-1", "0"])
def test_user_scoped_endpoint_rejects_invalid_user_id_values(
    session: requests.Session,
    base_url: str,
    admin_headers: dict[str, str],
    timeout_seconds: float,
    bad_user_id: str,
) -> None:
    headers = dict(admin_headers)
    headers["X-User-ID"] = bad_user_id
    response = session.get(
        f"{base_url}/api/v1/profile",
        headers=headers,
        timeout=timeout_seconds,
    )
    assert response.status_code == 400
