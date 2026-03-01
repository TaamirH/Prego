"""CLI entrypoint for the Prego technical exercise mapper."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from .mappers import map_charge, map_dispute, map_payout, map_refund
from .merge import finalize_bucket, upsert


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_output(input_dir: Path) -> Dict[str, Any]:
    charges: Dict[str, Dict[str, Any]] = {}
    disputes: Dict[str, Dict[str, Any]] = {}
    refunds: Dict[str, Dict[str, Any]] = {}
    payouts: Dict[str, Dict[str, Any]] = {}

    for file_path in sorted(input_dir.glob("*.json")):
        payload = load_json(file_path)
        object_type = str(payload.get("object", "")).lower()

        if object_type == "charge":
            record = map_charge(payload)
            upsert(charges, str(payload.get("id", "")), record, "charge")
            continue
        if object_type == "dispute":
            record = map_dispute(payload)
            upsert(disputes, str(payload.get("id", "")), record, "dispute")
            continue
        if object_type == "refund":
            record = map_refund(payload)
            upsert(refunds, str(payload.get("id", "")), record, "refund")
            continue
        if object_type == "payout":
            record = map_payout(payload)
            upsert(payouts, str(payload.get("id", "")), record, "payout")
            continue

    return {
        "transactions": list(finalize_bucket(charges, "transaction_id")),
        "disputes": list(finalize_bucket(disputes, "dispute_id")),
        "refunds": list(finalize_bucket(refunds, "refund_id")),
        "payouts": list(finalize_bucket(payouts, "payout_id")),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Map Stripe samples to Prego schema.")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path.cwd(),
        help="Directory containing Stripe-like JSON sample files.",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=Path("output.json"),
        help="Output JSON file path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = build_output(args.input_dir)
    with args.output_file.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()

