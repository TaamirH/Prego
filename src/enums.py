"""Allowed enums and normalization helpers for Prego mapping."""

from __future__ import annotations

from typing import Optional


TRANSACTION_STATUSES = {
    "authorized",
    "cancel_or_refund",
    "canceled",
    "capture",
    "deposit",
    "failed",
    "gateway_rejected",
    "paid",
    "pending",
    "processor_declined",
}

PAYMENT_METHODS = {"card", "apple pay", "paywithgoogle"}
CARD_TYPES = {"debit", "credit"}
NETWORKS = {"visa", "mastercard", "discover"}

DISPUTE_STATUSES = {"won", "lost", "pending"}
DISPUTE_REASONS = {"duplicate processing", "fraud", "stolen card"}

REFUND_STATUSES = {"success", "pending", "rejected"}
PAYOUT_STATUSES = {"paid", "pending", "canceled"}


def _clean(value: Optional[str]) -> str:
    if value is None:
        return ""
    return str(value).strip().lower().replace("_", " ")


def normalize_payment_method(value: Optional[str]) -> str:
    cleaned = _clean(value)
    alias_map = {
        "card": "card",
        "apple pay": "apple pay",
        "applepay": "apple pay",
        "google pay": "paywithgoogle",
        "googlepay": "paywithgoogle",
        "paywithgoogle": "paywithgoogle",
    }
    normalized = alias_map.get(cleaned, "card")
    return normalized if normalized in PAYMENT_METHODS else "card"


def normalize_card_type(value: Optional[str]) -> str:
    cleaned = _clean(value)
    if cleaned in CARD_TYPES:
        return cleaned
    return "credit"


def normalize_network(value: Optional[str]) -> str:
    cleaned = _clean(value)
    alias_map = {
        "visa": "visa",
        "mastercard": "mastercard",
        "discover": "discover",
    }
    normalized = alias_map.get(cleaned)
    if normalized in NETWORKS:
        return normalized
    return "visa"


def normalize_dispute_status(value: Optional[str]) -> str:
    cleaned = _clean(value)
    status_map = {
        "won": "won",
        "lost": "lost",
        "needs response": "pending",
        "warning needs response": "pending",
        "warning under review": "pending",
        "under review": "pending",
        "pending": "pending",
    }
    normalized = status_map.get(cleaned, "pending")
    return normalized if normalized in DISPUTE_STATUSES else "pending"


def normalize_dispute_reason(value: Optional[str]) -> str:
    cleaned = _clean(value)
    if "duplicate" in cleaned:
        return "duplicate processing"
    if "stolen" in cleaned:
        return "stolen card"
    if "fraud" in cleaned:
        return "fraud"
    return "fraud"


def normalize_refund_status(value: Optional[str]) -> str:
    cleaned = _clean(value)
    status_map = {
        "succeeded": "success",
        "success": "success",
        "pending": "pending",
        "failed": "rejected",
        "canceled": "rejected",
        "rejected": "rejected",
    }
    normalized = status_map.get(cleaned, "pending")
    return normalized if normalized in REFUND_STATUSES else "pending"


def normalize_payout_status(value: Optional[str]) -> str:
    cleaned = _clean(value)
    status_map = {
        "paid": "paid",
        "pending": "pending",
        "in transit": "pending",
        "canceled": "canceled",
    }
    normalized = status_map.get(cleaned, "pending")
    return normalized if normalized in PAYOUT_STATUSES else "pending"

