"""Stripe object to Prego schema mappers."""

from __future__ import annotations

from typing import Any, Dict

from .enums import (
    TRANSACTION_STATUSES,
    normalize_card_type,
    normalize_dispute_reason,
    normalize_dispute_status,
    normalize_network,
    normalize_payment_method,
    normalize_payout_status,
    normalize_refund_status,
)


def namespaced_id(stripe_id: str) -> str:
    return f"stripe_{stripe_id}"


def _normalize_token(value: Any, default: str) -> str:
    text = str(value).strip().lower() if value is not None else ""
    text = text.replace(" ", "_")
    return text or default


def map_charge(charge: Dict[str, Any]) -> Dict[str, Any]:
    status = _map_transaction_status(charge)
    payment_details = charge.get("payment_method_details") or {}
    card = payment_details.get("card") or {}
    outcome = charge.get("outcome") or {}

    response = outcome.get("reason")
    if not response:
        response = charge.get("failure_code")
    if not response:
        network_status = str(outcome.get("network_status") or "")
        response = "approved" if "approved" in network_status else "unknown"

    return {
        "_raw_id": str(charge.get("id", "")),
        "_created": int(charge.get("created", 0)),
        "transaction_id": namespaced_id(str(charge.get("id", ""))),
        "prego_status": status,
        "prego_payment_method": normalize_payment_method(payment_details.get("type")),
        "prego_card_type": normalize_card_type(card.get("funding")),
        "prego_transaction_response": _normalize_token(response, default="unknown"),
        "prego_network": normalize_network(card.get("network") or card.get("brand")),
    }


def _map_transaction_status(charge: Dict[str, Any]) -> str:
    stripe_status = str(charge.get("status", "")).lower()
    captured = bool(charge.get("captured", False))
    paid = bool(charge.get("paid", False))

    outcome = charge.get("outcome") or {}
    network_status = str(outcome.get("network_status", "")).lower()
    outcome_type = str(outcome.get("type", "")).lower()

    failure_code = charge.get("failure_code")

    if stripe_status == "failed":
        if failure_code or "declined" in network_status or "declined" in outcome_type:
            return "processor_declined"
        return "failed"

    if stripe_status == "succeeded":
        if not captured:
            return "authorized"
        if captured and paid:
            return "paid"
        return "capture"

    if stripe_status == "pending":
        return "pending"

    if stripe_status == "canceled":
        return "canceled"

    return "pending" if "pending" in TRANSACTION_STATUSES else "failed"


def map_dispute(dispute: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "_raw_id": str(dispute.get("id", "")),
        "_created": int(dispute.get("created", 0)),
        "dispute_id": namespaced_id(str(dispute.get("id", ""))),
        "prego_dispute_status": normalize_dispute_status(dispute.get("status")),
        "prego_dispute_reason": normalize_dispute_reason(dispute.get("reason")),
    }


def map_refund(refund: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "_raw_id": str(refund.get("id", "")),
        "_created": int(refund.get("created", 0)),
        "refund_id": namespaced_id(str(refund.get("id", ""))),
        "prego_refund_status": normalize_refund_status(refund.get("status")),
        # Enum list for refund reason was not provided; preserve normalized Stripe reason.
        "prego_refund_reason": _normalize_token(refund.get("reason"), default="not_provided"),
    }


def map_payout(payout: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "_raw_id": str(payout.get("id", "")),
        "_created": int(payout.get("created", 0)),
        "payout_id": namespaced_id(str(payout.get("id", ""))),
        "prego_payout_status": normalize_payout_status(payout.get("status")),
    }

