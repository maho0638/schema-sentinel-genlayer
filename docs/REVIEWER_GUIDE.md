# Reviewer guide — SchemaSentinel

## Five-minute walkthrough

1. Read `contracts/schema_sentinel.py` (one standalone contract).
2. In `README.md` confirm the constrained manifest grammar and why deterministic and semantic checks are separate.
3. In `tests/direct/test_schema_sentinel.py` inspect breaking changes, fail-closed ambiguity and independent validator disagreement.
4. Check `docs/THREAT_MODEL.md` for explicit vendor-authenticity and OpenAPI scope limitations.
5. Check `docs/PROOF_MANIFEST.json` for *verified* outcomes; missing live results must not be presented as deployment success.

## Reproduce

`python -m pip install -r requirements.txt`

- `python -m pytest tests/offline -q` — dependency-free stub logic smoke, no GenVM.
- `python -m pytest tests/direct -q` — real `genlayer-test` Direct Mode, mocked deterministic LLM responses and validator re-execution.
- `genvm-lint check contracts/schema_sentinel.py` — GenVM source syntax/compatibility.
- `.github/workflows/ci.yml` — automatic direct and lint on push.
- `.github/workflows/studionet.yml` — **manual**, real Studionet: register baseline, structural breaking assessment, semantic assessment, and on-chain readbacks.

## Expected semantics

| Candidate delta | Verdict | Why |
|---|---|---|
| No change / reordering | `COMPATIBLE` | Same canonical hash, no LLM |
| Add optional `IN`/`OUT` field | `COMPATIBLE` | Existing callers unaffected within this model |
| Add mandatory `IN` | `BREAKING` | Existing callers may omit it |
| Remove any existing field | `BREAKING` | Conservative contract guarantee |
| Change old output from required to optional | `BREAKING` | Existing readers may rely on it |
| Change old field description with high-confidence `SAME` consensus | `COMPATIBLE` | Validators agree on same behavior |
| Change description with `CHANGED` or low-confidence result | `REVIEW` | Manual review required |
| Leader says `SAME`, validator `CHANGED` | Consensus disagreement | No verified compatible record |

Production-readiness requires additional threat modeling and independently witnessed live validator transactions.
