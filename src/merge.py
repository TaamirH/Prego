"""Deterministic upsert/state merge logic."""

from __future__ import annotations

from typing import Dict, Tuple


RecordEnvelope = Dict[str, object]


TRANSACTION_STATUS_PRIORITY = {
    "authorized": 10,
    "pending": 20,
    "capture": 30,
    "paid": 40,
    "deposit": 50,
    "cancel_or_refund": 60,
    "failed": 70,
    "gateway_rejected": 80,
    "processor_declined": 90,
    "canceled": 100,
}


def _status_rank(record: RecordEnvelope, object_type: str) -> int:
    if object_type != "charge":
        return 0
    status = str(record.get("prego_status", "pending"))
    return TRANSACTION_STATUS_PRIORITY.get(status, 0)


def should_replace(existing: RecordEnvelope, candidate: RecordEnvelope, object_type: str) -> bool:
    """Return True if candidate should replace existing deterministically."""
    existing_created = int(existing.get("_created", 0))
    candidate_created = int(candidate.get("_created", 0))

    if candidate_created > existing_created:
        return True
    if candidate_created < existing_created:
        return False

    existing_rank = _status_rank(existing, object_type)
    candidate_rank = _status_rank(candidate, object_type)
    if candidate_rank > existing_rank:
        return True
    if candidate_rank < existing_rank:
        return False

    existing_key = str(existing.get("_raw_id", ""))
    candidate_key = str(candidate.get("_raw_id", ""))
    return candidate_key >= existing_key


def upsert(
    bucket: Dict[str, RecordEnvelope],
    key: str,
    value: RecordEnvelope,
    object_type: str,
) -> None:
    existing = bucket.get(key)
    if existing is None or should_replace(existing, value, object_type):
        bucket[key] = value


def strip_internal_fields(record: RecordEnvelope) -> RecordEnvelope:
    return {k: v for k, v in record.items() if not k.startswith("_")}


def finalize_bucket(bucket: Dict[str, RecordEnvelope], id_field: str) -> Tuple[RecordEnvelope, ...]:
    records = [strip_internal_fields(v) for _, v in sorted(bucket.items(), key=lambda item: item[0])]
    return tuple(sorted(records, key=lambda row: str(row.get(id_field, ""))))

