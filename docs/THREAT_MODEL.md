# Security and limitations

**Trust boundary:** any address can register arbitrary baselines and submit candidates. IDs and SHA-256 hashes identify caller-chosen material, *not* vendor signatures, hosting, domain identity or public API truth. A consumer must first trust the chosen baseline ID and its creator out of band.

| Risk | Control / limitation |
|---|---|
| Malformed manifests / oversized data | Bounded input, closed enums, strict duplicate rejection and unique field keys; reject before storage mutation. |
| Hash ambiguity | Canonical sorted field list, explicit `|` separators and SHA-256 for frozen baseline, candidate, and change list. |
| Prompt injection in descriptions | Descriptions treated as untrusted data; output restricted to decisions, validated and independently re-evaluated. This is a risk reduction, not a complete LLM security guarantee. |
| Validator disagreeing about same meaning | Compare normalized decisive class; changes across confidence threshold or semantic class cause disagreement, rather than silently accepting a flip. |
| Low confidence or invalid AI JSON | `UNKNOWN` → `REVIEW`; cannot silently become compatible. |
| Replay / duplicate receipt | Immutable receipt IDs and baseline IDs. |
| Model abuse / call costs | Maximum 16 fields and no LLM invocation on purely structural changes. GenLayer gas/LLM costs are network dependent. |
| Missing OpenAPI features | Flat one-operation field manifests only; no JSON Schema refs, discriminated unions, arrays-of-type, auth headers, error codes, semantic versioning or protocol compatibility proof. |
| Structural false positives | Conservative rule considers field removal breaking even if an API may tolerate it. |
| Structural false negatives | Descriptions cannot express full runtime behavior, authorization, server error modes or contractual guarantees. |
| Real-chain availability | Integration proof must be run and observed; offline tests cannot certify deployed validator consensus. |

No pooled GEN, user funds, router, oracle secret, URL fetching, network-level SSRF or permissioned withdrawal path exists. The contract is a release-check primitive, **not an on-chain API runtime monitor**.
