"""Profile and address endpoint tests."""

from __future__ import annotations

import uuid

import requests


def test_get_profile_success(
    session: requests.Session,
    base_url: str,
    user_headers: dict[str, str],
    timeout_seconds: float,
) -> None:
    response = session.get(
        f"{base_url}/api/v1/profile",
        headers=user_headers,
        timeout=timeout_seconds,
    )
    assert response.status_code == 200
    assert isinstance(response.json(), dict)


def test_update_profile_invalid_phone_rejected(
    session: requests.Session,
    base_url: str,
    user_headers: dict[str, str],
    timeout_seconds: float,
) -> None:
    payload = {"name": "Valid Name", "phone": "12345"}
    response = session.put(
        f"{base_url}/api/v1/profile",
        headers=user_headers,
        json=payload,
        timeout=timeout_seconds,
    )
    assert response.status_code == 400


def test_add_address_invalid_label_rejected(
    session: requests.Session,
    base_url: str,
    user_headers: dict[str, str],
    timeout_seconds: float,
) -> None:
    payload = {
        "label": "HOSTEL",
        "street": "12345 Long Street",
        "city": "Hyderabad",
        "pincode": "500001",
        "is_default": False,
    }
    response = session.post(
        f"{base_url}/api/v1/addresses",
        headers=user_headers,
        json=payload,
        timeout=timeout_seconds,
    )
    assert response.status_code == 400


def test_add_address_missing_required_field_rejected(
    session: requests.Session,
    base_url: str,
    user_headers: dict[str, str],
    timeout_seconds: float,
) -> None:
    payload = {
        "label": "HOME",
        "street": "12345 Long Street",
        "city": "Hyderabad",
        # pincode missing on purpose
        "is_default": False,
    }
    response = session.post(
        f"{base_url}/api/v1/addresses",
        headers=user_headers,
        json=payload,
        timeout=timeout_seconds,
    )
    assert response.status_code == 400


def test_add_address_valid_and_delete(
    session: requests.Session,
    base_url: str,
    user_headers: dict[str, str],
    timeout_seconds: float,
) -> None:
    payload = {
        "label": "OTHER",
        "street": f"Test Street {uuid.uuid4().hex[:8]}",
        "city": "Hyderabad",
        "pincode": "500001",
        "is_default": False,
    }
    create = session.post(
        f"{base_url}/api/v1/addresses",
        headers=user_headers,
        json=payload,
        timeout=timeout_seconds,
    )
    assert create.status_code in (200, 201)
    body = create.json()
    assert isinstance(body, dict)

    address = body.get("address") if isinstance(body.get("address"), dict) else body
    address_id = address.get("address_id") if isinstance(address, dict) else None
    assert isinstance(address_id, int)

    delete = session.delete(
        f"{base_url}/api/v1/addresses/{address_id}",
        headers=user_headers,
        timeout=timeout_seconds,
    )
    assert delete.status_code == 200


def test_update_address_forbidden_fields_rejected(
    session: requests.Session,
    base_url: str,
    user_headers: dict[str, str],
    timeout_seconds: float,
) -> None:
    payload = {
        "label": "HOME",
        "street": f"Update Street {uuid.uuid4().hex[:8]}",
        "city": "Hyderabad",
        "pincode": "500001",
        "is_default": False,
    }
    create = session.post(
        f"{base_url}/api/v1/addresses",
        headers=user_headers,
        json=payload,
        timeout=timeout_seconds,
    )
    assert create.status_code in (200, 201)
    created = create.json()
    address = (
        created.get("address")
        if isinstance(created, dict) and isinstance(created.get("address"), dict)
        else created
    )
    address_id = address.get("address_id") if isinstance(address, dict) else None
    assert isinstance(address_id, int)

    bad_update = {
        "label": "OFFICE",  # should not be updatable as per doc
        "street": "Updated Street 123",
        "city": "Bengaluru",
    }
    response = session.put(
        f"{base_url}/api/v1/addresses/{address_id}",
        headers=user_headers,
        json=bad_update,
        timeout=timeout_seconds,
    )
    assert response.status_code == 400

    session.delete(
        f"{base_url}/api/v1/addresses/{address_id}",
        headers=user_headers,
        timeout=timeout_seconds,
    )
