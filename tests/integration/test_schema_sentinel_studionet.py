"""Manual real-Studionet proof; never silently invoked by regular CI."""
import hashlib
import pytest
from gltest import get_contract_factory
from gltest.assertions import tx_execution_succeeded

BASE = "IN|user_id|string|1|Account identifier\nOUT|active|boolean|1|Whether account is active"


def field(result, name):
    return result.get(name) if isinstance(result, dict) else getattr(result, name)


@pytest.mark.integration
def test_schema_sentinel_real_consensus_lifecycle(default_account):
    contract = get_contract_factory("SchemaSentinel").deploy(account=default_account, consensus_max_rotations=4)
    print("SCHEMA_SENTINEL_ADDRESS=" + str(contract.address), flush=True)
    tx = contract.register_baseline(args=["endpoint-v1", "GET /users/{id}", BASE]).transact(wait_interval=10000, wait_retries=50)
    assert tx_execution_succeeded(tx)
    print("REGISTER_TX=" + str(tx.get("hash", "")), flush=True)

    baseline = contract.get_baseline(args=["endpoint-v1"]).call()
    assert str(field(baseline, "schema_hash")) == hashlib.sha256(str(field(baseline, "canonical_schema")).encode()).hexdigest()

    breaking = BASE.replace("active|boolean|1", "active|string|1")
    tx = contract.assess(args=["receipt-breaking", "endpoint-v1", breaking]).transact(wait_interval=10000, wait_retries=50)
    assert tx_execution_succeeded(tx)
    print("BREAKING_TX=" + str(tx.get("hash", "")), flush=True)
    r = contract.get_receipt(args=["receipt-breaking"]).call()
    assert str(field(r, "verdict")) == "BREAKING"
    assert int(field(r, "breaking_count")) == 1

    semantic_candidate = BASE.replace("Whether account is active", "Whether this account is currently active")
    tx = contract.assess(args=["receipt-semantic", "endpoint-v1", semantic_candidate]).transact(
        consensus_max_rotations=4, wait_interval=10000, wait_retries=80
    )
    assert tx_execution_succeeded(tx)
    print("SEMANTIC_TX=" + str(tx.get("hash", "")), flush=True)
    semantic = contract.get_receipt(args=["receipt-semantic"]).call()
    assert str(field(semantic, "semantic_status")) in ("SAME", "CHANGED", "UNKNOWN")
    assert str(field(semantic, "verdict")) in ("COMPATIBLE", "REVIEW")
    assert str(field(semantic, "baseline_hash")) == str(field(baseline, "schema_hash"))
    print("SEMANTIC_VERDICT=" + str(field(semantic, "verdict")), flush=True)
