# Prego Technical Exercise

This project takes Stripe-style JSON files and converts them into Prego's format.
The script reads all input files, maps the fields, merges lifecycle updates, and writes one final `output.json`.

## Time spent

Around **1 hour 35 minutes** of active work.

## How I run it

From the project root:

```bash
python -m src.main --input-dir "c:\Users\taami\Downloads\Prego Technical Exercise\Prego Technical Exercise" --output-file "c:\Users\taami\OneDrive\Documents\Prego\output.json"
```

If I skip `--input-dir`, it reads all `*.json` files in the current folder.

## Output format

The script always writes:

```json
{
  "transactions": [],
  "disputes": [],
  "refunds": [],
  "payouts": []
}
```

## Mapping logic (simple version)

### 1) Transactions (from `charge`)

- `transaction_id` comes from `charge.id` and is namespaced: `stripe_<id>`.
- `prego_status` is based mainly on `status`, `captured`, and `paid`:
  - failed + decline signal -> `processor_declined`
  - succeeded + not captured -> `authorized`
  - succeeded + captured + paid -> `paid`
  - succeeded + captured + not paid -> `capture`
  - pending -> `pending`
- `prego_payment_method` uses `payment_method_details.type`.
- `prego_card_type` uses `payment_method_details.card.funding`.
- `prego_network` uses `payment_method_details.card.network` (fallback: brand).
- `prego_transaction_response` uses:
  `outcome.reason` -> `failure_code` -> approval/unknown fallback.

### 2) Disputes (from `dispute`)

- `dispute_id` = `stripe_<dispute.id>`
- `prego_dispute_status` maps Stripe statuses like `needs_response` to `pending`.
- `prego_dispute_reason` maps text to:
  - duplicate -> `duplicate processing`
  - stolen -> `stolen card`
  - fraud -> `fraud`

### 3) Refunds (from `refund`)

- `refund_id` = `stripe_<refund.id>`
- `prego_refund_status`:
  - succeeded -> `success`
  - pending -> `pending`
  - failed/canceled -> `rejected`
- `prego_refund_reason` keeps Stripe reason in normalized token form (or `not_provided`).

### 4) Payouts (from `payout`)

- `payout_id` = `stripe_<payout.id>`
- `prego_payout_status` normalized to: `paid`, `pending`, or `canceled`

## ID strategy

I used a simple deterministic format for all objects:

- `stripe_<stripe_object_id>`

Examples:
- `stripe_ch_3PREG0Auth0001`
- `stripe_dp_3PREG0Dispute0001`
- `stripe_re_3PREG0Refund0001`
- `stripe_po_3PREG0Payout0001`

Why: it is stable and easy to track, and it avoids collisions if another payment provider is added later.

## Lifecycle merge (upsert)

Some files can represent different stages of the same object (for example one charge being first authorized, then captured).

To handle that, I upsert by raw Stripe ID:
1. Keep one record per object ID.
2. Prefer the one with larger `created`.
3. If timestamps are equal, use status priority as a deterministic tie-breaker.

So the final `output.json` has only the latest state per ID.

## Assumptions

- The enum values provided in the exercise instructions are the source of truth.
- `prego_transaction_response` and `prego_refund_reason` did not have a strict enum list in the provided files, so I used normalized Stripe-derived values.
- For unknown/unexpected inputs, deterministic fallbacks are used:
  - payment method -> `card`
  - card type -> `credit`
  - network -> `visa`
  - dispute reason -> `fraud`

## If I had another day on this

- Add a small `tests/` suite with clear pass/fail cases for each mapper.
- Read mapping rules from a config file so enum/rule changes do not require code edits.
- Add a validation script that checks `output.json` before submission.
- Improve logging so every fallback decision is visible and easy to debug.

