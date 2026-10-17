# Architecture — one bounded, auditable state machine

## Storage

`SchemaBaseline[id] = (operation, canonical_schema, sha256(canonical_schema))`. Registration is public and irreversible for a given ID. The baseline hash is checked again before every assessment.

`CompatibilityReceipt[id] = (baseline_id, baseline_hash, candidate_hash, changes_hash, breaking_count, addition_count, changed_descriptions, semantic_status, verdict)`. Receipt IDs are unique; repeated assessments must use new IDs. No reset, overwrite, or mutable review state exists.

## Deterministic boundary

The source parser enforces a closed vocabulary, maximum 16 fields and 3,600 input characters, unique `(direction,name)` keys, and 5-part `|` records. Schema order is irrelevant to SHA-256. The diff handles additions, removals, requiredness and type changes without AI.

- Removed existing request or response field → `BREAKING` (conservative: older clients may still send removed inputs).
- Any type change → `BREAKING`.
- New required `IN` field, or existing `IN` `0→1` → `BREAKING`.
- Existing `OUT` `1→0` → `BREAKING`.
- Other added fields and relaxations → not structurally breaking.
- No changed old descriptions → `COMPATIBLE` if no hard breaks.

## Nondeterministic boundary

When existing descriptions change but structural checks do not break:

1. Build the bounded old/new field-description diff from frozen state.
2. Leader asks `gl.nondet.exec_prompt(..., response_format='json')` for `SAME`, `CHANGED`, `UNKNOWN` and integer confidence 0–100.
3. Malformed output, malformed confidence, confidence below 70, or unresolved meaning normalizes to `UNKNOWN`.
4. Validator independently re-runs the same question and compares normalized decision class. Different decisive class → `False`, rather than trusting the leader's prose or raw score.
5. `SAME` → `COMPATIBLE`; `CHANGED` or `UNKNOWN` → `REVIEW`. GenLayer consensus must also succeed for state to be committed.

Hard-break and no-semantic-change paths **do not invoke** the model at all. No untrusted HTML, web browser, or native GEN transfer is required.

## Receipts and downstream use

`is_compatible(receipt_id)` is true only for the `COMPATIBLE` decision; it is false for `BREAKING` and `REVIEW`. A receipt contains the immutable hashes so off-chain release automation can associate it with known API release artifacts. The contract cannot itself prove that external servers serve the assessed schema.
