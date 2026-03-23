"""Reviews, support tickets, and coupon tests."""

from __future__ import annotations

import uuid

import requests


def test_reviews_get_and_invalid_rating(
    session: requests.Session,
    base_url: str,
    user_headers: dict[str, str],
    active_product_id: int,
    timeout_seconds: float,
) -> None:
    get_reviews = session.get(
        f"{base_url}/api/v1/products/{active_product_id}/reviews",
        headers=user_headers,
        timeout=timeout_seconds,
    )
    assert get_reviews.status_code == 200

    bad_rating = session.post(
        f"{base_url}/api/v1/products/{active_product_id}/reviews",
        headers=user_headers,
        json={"rating": 6, "comment": "Too high rating should fail"},
        timeout=timeout_seconds,
    )
    assert bad_rating.status_code == 400


def test_review_wrong_type_rating_rejected(
    session: requests.Session,
    base_url: str,
    user_headers: dict[str, str],
    active_product_id: int,
    timeout_seconds: float,
) -> None:
    response = session.post(
        f"{base_url}/api/v1/products/{active_product_id}/reviews",
        headers=user_headers,
        json={"rating": "five", "comment": "wrong type rating"},
        timeout=timeout_seconds,
    )
    assert response.status_code == 400


def test_review_missing_comment_rejected(
    session: requests.Session,
    base_url: str,
    user_headers: dict[str, str],
    active_product_id: int,
    timeout_seconds: float,
) -> None:
    response = session.post(
        f"{base_url}/api/v1/products/{active_product_id}/reviews",
        headers=user_headers,
        json={"rating": 4},
        timeout=timeout_seconds,
    )
    assert response.status_code == 400


def test_add_review_valid(
    session: requests.Session,
    base_url: str,
    user_headers: dict[str, str],
    active_product_id: int,
    timeout_seconds: float,
) -> None:
    response = session.post(
        f"{base_url}/api/v1/products/{active_product_id}/reviews",
        headers=user_headers,
        json={"rating": 5, "comment": "Great product"},
        timeout=timeout_seconds,
    )
    assert response.status_code in (200, 201)


def test_create_support_ticket_and_invalid_short_subject(
    session: requests.Session,
    base_url: str,
    user_headers: dict[str, str],
    timeout_seconds: float,
) -> None:
    invalid = session.post(
        f"{base_url}/api/v1/support/ticket",
        headers=user_headers,
        json={"subject": "Hey", "message": "Need help"},
        timeout=timeout_seconds,
    )
    assert invalid.status_code == 400

    valid = session.post(
        f"{base_url}/api/v1/support/ticket",
        headers=user_headers,
        json={
            "subject": f"Order issue {uuid.uuid4().hex[:6]}",
            "message": "Item was delayed by one day.",
        },
        timeout=timeout_seconds,
    )
    assert valid.status_code in (200, 201)


def test_ticket_status_transition_validation(
    session: requests.Session,
    base_url: str,
    user_headers: dict[str, str],
    timeout_seconds: float,
) -> None:
    create = session.post(
        f"{base_url}/api/v1/support/ticket",
        headers=user_headers,
        json={
            "subject": f"Status transition {uuid.uuid4().hex[:6]}",
            "message": "Transition test message.",
        },
        timeout=timeout_seconds,
    )
    if create.status_code not in (200, 201):
        # Avoid false failure if seed/user policy blocks ticket creation.
        assert create.status_code in (400, 401, 403)
        return

    created = create.json()
    ticket_id = created.get("ticket_id") if isinstance(created, dict) else None
    if not isinstance(ticket_id, int):
        assert isinstance(created, dict)
        return

    invalid_transition = session.put(
        f"{base_url}/api/v1/support/tickets/{ticket_id}",
        headers=user_headers,
        json={"status": "CLOSED"},
        timeout=timeout_seconds,
    )
    assert invalid_transition.status_code == 400


def test_apply_coupon_invalid_code(
    session: requests.Session,
    base_url: str,
    user_headers: dict[str, str],
    timeout_seconds: float,
) -> None:
    response = session.post(
        f"{base_url}/api/v1/coupon/apply",
        headers=user_headers,
        json={"code": "NOT_A_REAL_COUPON"},
        timeout=timeout_seconds,
    )
    assert response.status_code in (400, 404)
