# Prego Technical Exercise

This project maps Stripe-like JSON objects into Prego's internal schema and writes a consolidated `output.json`.

## Active working time

Approximately **1 hour 35 minutes**.

## How to run

From the project root:

```bash
python -m src.main --input-dir "c:\Users\taami\Downloads\Prego Technical Exercise\Prego Technical Exercise" --output-file "c:\Users\taami\OneDrive\Documents\Prego\output.json"
```

If `--input-dir` is omitted, the program reads `*.json` in the current directory.

## Stripe fields used and mapping rationale

### Transactions (`charge` -> `transactions[]`)

- `transaction_id`
  - Source: `charge.id`
  - Rule: namespaced deterministic ID `stripe_<charge.id>`.

- `prego_status`
  - Source: `charge.status`, `charge.captured`, `charge.paid`, plus decline indicators from `outcome` and `failure_code`.
  - Rules:
    - `status=failed` with decline indicators -> `processor_declined`
    - `status=succeeded` and `captured=false` -> `authorized`
    - `status=succeeded`, `captured=true`, `paid=true` -> `paid`
    - `status=pending` -> `pending`
    - fallback -> `pending`

- `prego_payment_method`
  - Source: `payment_method_details.type`
  - Rule: normalized aliases into allowed set (`card`, `apple pay`, `paywithgoogle`).

- `prego_card_type`
  - Source: `payment_method_details.card.funding`
  - Rule: normalized to `credit` or `debit`.

- `prego_network`
  - Source: `payment_method_details.card.network` (fallback `brand`)
  - Rule: normalized to allowed set (`visa`, `mastercard`, `discover`).

- `prego_transaction_response`
  - Source priority: `outcome.reason` -> `failure_code` -> inferred success token from `outcome.network_status`.
  - Rule: normalized to lowercase underscore tokens (example: `insufficient_funds`, `approved`).

### Disputes (`dispute` -> `disputes[]`)

- `dispute_id`
  - Source: `dispute.id`
  - Rule: namespaced deterministic ID `stripe_<dispute.id>`.

- `prego_dispute_status`
  - Source: `dispute.status`
  - Rule: Stripe values like `needs_response` map to `pending`; direct `won`/`lost` preserved.

- `prego_dispute_reason`
  - Source: `dispute.reason`
  - Rule: keyword normalization to allowed set:
    - contains `duplicate` -> `duplicate processing`
    - contains `stolen` -> `stolen card`
    - contains `fraud` -> `fraud`
    - fallback -> `fraud`

### Refunds (`refund` -> `refunds[]`)

- `refund_id`
  - Source: `refund.id`
  - Rule: namespaced deterministic ID `stripe_<refund.id>`.

- `prego_refund_status`
  - Source: `refund.status`
  - Rule:
    - `succeeded` -> `success`
    - `pending` -> `pending`
    - `failed`/`canceled` -> `rejected`

- `prego_refund_reason`
  - Source: `refund.reason`
  - Rule: normalized lowercase underscore token (fallback `not_provided`).

### Payouts (`payout` -> `payouts[]`)

- `payout_id`
  - Source: `payout.id`
  - Rule: namespaced deterministic ID `stripe_<payout.id>`.

- `prego_payout_status`
  - Source: `payout.status`
  - Rule: normalized to `paid`, `pending`, or `canceled`.

## Deterministic ID design

All IDs are generated as:

- `stripe_<stripe_object_id>`

Examples:

- `stripe_ch_3PREG0Auth0001`
- `stripe_re_3PREG0Refund0001`
- `stripe_dp_3PREG0Dispute0001`
- `stripe_po_3PREG0Payout0001`

This guarantees deterministic keys and avoids collisions if additional processors are introduced later.

## Lifecycle handling / upsert logic

Some charge samples represent different lifecycle stages of the same transaction (`authorized` and later `captured/paid` share the same Stripe charge ID). The mapper performs state merging:

1. Upsert by raw Stripe object ID.
2. Prefer record with higher `created` timestamp.
3. If tied, apply deterministic status priority for transaction statuses.

This yields one final latest-state record per object ID in `output.json`.

## Assumptions

- The allowed enum sets supplied in the instructions are authoritative.
- `prego_transaction_response` and `prego_refund_reason` did not include explicit allowed value lists in provided materials, so normalized Stripe-derived tokens are used.
- Where Stripe values fall outside known aliases, deterministic defaults are applied:
  - payment method fallback: `card`
  - card type fallback: `credit`
  - network fallback: `visa`
  - dispute reason fallback: `fraud`

## What I would improve with more time

- Add schema validation and unit tests for each mapper function and edge cases.
- Add explicit config-driven enum maps loaded from CSV/XLSX rather than hardcoded values.
- Add a small test harness that replays lifecycle events in random order to prove upsert determinism.
- Add structured logging and warning output for every fallback/default mapping.

