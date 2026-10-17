# SchemaSentinel — API Compatibility Consensus for GenLayer

**A standalone, reusable GenLayer Intelligent Contract:** freeze a bounded API field manifest, compare future versions deterministically, and let independent GenLayer validators examine only the hard-to-automate *semantic drift* of existing field descriptions. It produces immutable, hash-bound compatibility receipts.

The contract has no token escrow, embedded private keys, key custody, frontend or external URL fetch. Normal signed transactions still require a GenLayer account.

## Problem

An API upgrade can look compatible at the schema/type level yet silently redefine `balance` from *available balance* to *lifetime balance*. Conversely, harmless wording changes should not be rejected as hard breaks. Traditional on-chain code can analyze field shapes but cannot judge semantic equivalence of changed descriptions. An unrestricted AI verdict is too easy to manipulate.

**SchemaSentinel keeps the boundary explicit:**

- **Deterministic breaking rules**: removed field, changed type, optional input becoming required, required output becoming optional, newly added required input.
- **Deterministic compatible rules**: unchanged manifest or added optional input/output, assuming no other changes.
- **Semantic consensus only when needed**: if the field shape is compatible but an existing field description changes, validators independently classify `SAME`, `CHANGED`, or `UNKNOWN` using `gl.vm.run_nondet_unsafe`. Only consensus-backed `SAME` can yield `COMPATIBLE`. Other outcomes yield `REVIEW` (fail closed).
- **Immutable audit bindings**: canonical baseline SHA-256, candidate SHA-256, deterministic changes SHA-256, breaking/addition counts, and semantic status.

A `BREAKING` verdict is deterministic and never depends on an LLM. This is a small primitive, **not** a full OpenAPI 3.x implementation or formal protocol compatibility proof.

## Minimal working example

Each nonempty line is `DIRECTION|field_name|type|required|description`:

```text
IN|user_id|string|1|Account identifier
OUT|active|boolean|1|Whether account is active
```

- `DIRECTION`: `IN` (request) or `OUT` (response).
- `field_name`: lowercase letters, digits, `.`, `_`, `-` (max 64 characters).
- `type`: `string`, `integer`, `boolean`, `decimal`, `object`, `array`.
- `required`: `1` (required) or `0` (optional).
- `description`: 1–160 characters, no `|` or embedded newline.
- 1–16 unique fields, maximum 3,600 characters total. Ordering and leading/trailing whitespace are canonicalized; different field order yields the same hash.

On GenLayer:

1. `register_baseline("users-v1", "GET /users/{id}", baseline_manifest)` — permanently freezes the manifest and its hash.
2. `assess("release-2", "users-v1", candidate_manifest)` — stores an immutable receipt.
3. `get_receipt("release-2")`, `get_baseline("users-v1")`, `is_compatible("release-2")` — read receipt, frozen baseline, or boolean gate.

**Decisions:** `COMPATIBLE`, `BREAKING`, `REVIEW`. Treat `REVIEW` as **not authorized** for any compatibility-sensitive automation. Review is not an approval.

## Why real GenLayer consensus matters

The hard part is semantic equivalence. A leader can understand two natural-language descriptions, but other validators must be able to independently disagree. The validator re-runs the exact constrained evaluation on the same immutable before/after evidence, normalizes malformed or low-confidence output to `UNKNOWN`, and compares the *decision class*, not superficial prose or raw confidence. A threshold crossing (`SAME` at 90 vs `SAME` at 60) changes the class and causes disagreement. Minor non-decisive confidence drift can still agree.

See [architecture](docs/ARCHITECTURE.md), [security limitations](docs/THREAT_MODEL.md), [reviewer reproduction](docs/REVIEWER_GUIDE.md), and [Portal draft](SUBMISSION_DRAFT.md).

## Verification status (17 October 2026)

**Verified:** 40/40 genuine GenLayer Direct Mode tests, GenVM lint 3/3, and 1/1 live Studionet integration lifecycle. The live test deployed SchemaSentinel, registered a baseline, recorded a deterministic `BREAKING` receipt, ran the semantic consensus assessment, read a `COMPATIBLE` result and checked its immutable baseline hash.

- Direct + lint: https://github.com/maho0638/schema-sentinel-genlayer/actions/runs/39018311313
- Live Studionet: https://github.com/maho0638/schema-sentinel-genlayer/actions/runs/39018478065
- Observed Studio contract: `0x5572D22D44F3a296d295bCa78B94e178bA996af9`
- Pinned SHA-256: `ee64774f75eceff8f1e702a4b19d9acb494a4de5f1a92f863eeeb0ad513e91ce`
- Full transaction hashes and observed outputs: [`docs/PROOF_MANIFEST.json`](docs/PROOF_MANIFEST.json).

Offline stub tests are **logic-only**, not network or consensus proof. Direct Mode uses controlled LLM mocks; the Studionet test is the separate observed live proof. No Bradbury or mainnet deployment is claimed.

```bash
python -m pip install -r requirements.txt
python -m pytest tests/offline -q
python -m pytest tests/direct -q
genvm-lint check contracts/schema_sentinel.py
```

Run the **manual** `SchemaSentinel Studionet Proof` GitHub Action only after direct checks succeed. No automatic live deployments occur from a regular push.

## Scope and provenance

Schema manifests are **caller-authored**; this contract does not authenticate a vendor, fetch canonical OpenAPI specifications, resolve references, model every OpenAPI compatibility rule, or guarantee runtime backward compatibility. Strict field checks are conservative. Semantic judgments can disagree, in which case consensus may reject or the result is `REVIEW` — never a speculative safe upgrade.

Built specifically for the GenLayer Portal **Intelligent Contracts** category as a standalone educational/reusable primitive. Unrelated to Sightline, VerdictMesh, TurnMaster or SemanticEscrow source code.
