# GenLayer Portal — Intelligent Contracts draft (do not submit before verifying CI)

**Title:** SchemaSentinel — Consensus-Verified API Compatibility Receipts

**Category:** Intelligent Contracts (standalone; no frontend)

**Pitch:** SchemaSentinel turns a versioned API field manifest into an immutable, hash-linked compatibility decision. Deterministic logic flags structurally breaking changes—removed or retyped fields, new mandatory inputs, weakened mandatory outputs—without invoking AI. When a field retains its type but its meaning may have changed, GenLayer validators independently compare the old and new natural-language descriptions and agree only on a bounded decision. Invalid or low-confidence results fail closed to `REVIEW`, never silent compatibility.

**Reusable use case:** Package maintainers, agent tool developers and API integrators can use the receipt to gate releases or request manual review before automated clients adopt an update. Both input and output changes are modeled in a compact deterministic, order-independent manifest.

**Consensus mechanism:** `gl.vm.run_nondet_unsafe` with independent `gl.nondet.exec_prompt` on validator. Compare normalized semantic classes after 70% confidence threshold; disagreement returns `False`. Deterministic structural breaks bypass LLM entirely.

**Evidence:** Source, Direct Mode tests, GenVM lint results, manual Studionet integration test and threat model in the repository. Publish CI/live URLs **only when actually successful**. Source hash and transaction addresses must come from observed runs.

**Known boundaries:** Not an OpenAPI parser, vendor identity attestor or live API monitor. No tokens/gas wallet management by the contract, no external website fetch, no source-authenticity guarantee. Caller must trust the baseline they select.
