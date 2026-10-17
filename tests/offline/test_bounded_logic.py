"""Dependency-free contract-logic smoke tests using a stub SDK.

These are NOT GenVM tests. CI additionally runs genuine genlayer-test Direct Mode.
"""
import importlib.util
import pathlib
import sys
import types

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE = "IN|user_id|string|1|Account identifier\nOUT|active|boolean|1|Whether account is active"


@pytest.fixture(scope="module")
def sdk():
    fake = types.ModuleType("genlayer")

    class UserError(Exception):
        pass

    class Return:
        def __init__(self, calldata):
            self.calldata = calldata

    fake.gl = types.SimpleNamespace(
        Contract=object,
        public=types.SimpleNamespace(write=lambda x: x, view=lambda x: x),
        nondet=types.SimpleNamespace(exec_prompt=lambda *args, **kwargs: {"status": "SAME", "confidence": 90}),
        vm=types.SimpleNamespace(UserError=UserError, Return=Return, run_nondet_unsafe=lambda leader, validator: leader()),
    )
    fake.allow_storage = lambda cls: cls
    fake.dataclass = __import__("dataclasses").dataclass
    fake.u256 = int

    class TreeMap(dict):
        def __class_getitem__(cls, args):
            return cls
    fake.TreeMap = TreeMap

    sys.modules["genlayer"] = fake
    spec = importlib.util.spec_from_file_location("local_schema_contract", ROOT / "contracts" / "schema_sentinel.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    yield module
    sys.modules.pop("genlayer", None)
    sys.modules.pop(spec.name, None)


def fresh(sdk):
    c = sdk.SchemaSentinel()
    c.baselines, c.receipts = {}, {}
    c.register_baseline("users-v1", "GET /users/{id}", BASE)
    return c


def test_baseline_immutable_canonical(sdk):
    c = fresh(sdk)
    assert c.get_baseline("users-v1").canonical_schema == BASE
    with pytest.raises(sdk.gl.vm.UserError):
        c.register_baseline("users-v1", "GET /x", BASE)


@pytest.mark.parametrize("candidate,expected", [
    (BASE, "COMPATIBLE"),
    (BASE + "\nIN|meta|boolean|0|Whether to include metadata", "COMPATIBLE"),
    (BASE + "\nIN|meta|boolean|1|Must provide metadata", "BREAKING"),
    (BASE.replace("boolean|1", "boolean|0"), "BREAKING"),
    (BASE.replace("boolean|1", "string|1"), "BREAKING"),
    (BASE.replace("OUT|active|boolean|1|Whether account is active", "" ).strip(), "BREAKING"),
    (BASE.replace("Whether account is active", "Whether this account is active"), "COMPATIBLE"),
])
def test_offline_lifecycle(sdk, candidate, expected):
    c = fresh(sdk)
    c.assess("r1", "users-v1", candidate)
    assert c.get_receipt("r1").verdict == expected
    assert c.is_compatible("r1") == (expected == "COMPATIBLE")


@pytest.mark.parametrize("candidate", [
    "IN|x|string|2|bad required", "IN|x|float|1|bad type",
    "IN|x|string|1|n\nIN|x|string|1|dup", "\n", "IN|x|string|1|note\n\nOUT|y|string|1|other",
    "IN|x|string|1|" + "a" * 161,
    "IN|x|string|1|ok\n" * 17,
])
def test_offline_invalid_schema(sdk, candidate):
    c = fresh(sdk)
    with pytest.raises(sdk.gl.vm.UserError):
        c.assess("bad", "users-v1", candidate)


def test_semantic_ambiguity_fails_closed(sdk):
    c = fresh(sdk)
    sdk.gl.nondet.exec_prompt = lambda *args, **kwargs: {"status": "SAME", "confidence": 40}
    c.assess("ambiguous", "users-v1", BASE.replace("active", "verified"))
    assert c.get_receipt("ambiguous").verdict == "BREAKING" # field renamed
    c.assess("ambiguous2", "users-v1", BASE.replace("Whether account is active", "Whether account is verified"))
    assert c.get_receipt("ambiguous2").verdict == "REVIEW"
    sdk.gl.nondet.exec_prompt = lambda *args, **kwargs: {"status": "SAME", "confidence": 90}


def test_mutated_baseline_detected(sdk):
    c = fresh(sdk)
    c.baselines["users-v1"].canonical_schema = BASE.replace("boolean", "string")
    with pytest.raises(sdk.gl.vm.UserError, match="Baseline integrity mismatch"):
        c.assess("mutated", "users-v1", BASE)


def test_reject_invalid_identifier(sdk):
    c = fresh(sdk)
    with pytest.raises(sdk.gl.vm.UserError):
        c.assess("../evil", "users-v1", BASE)


def test_validator_rejects_different_semantic_outcome(sdk):
    c = fresh(sdk)
    votes = iter([{"status": "SAME", "confidence": 95}, {"status": "CHANGED", "confidence": 95}])
    sdk.gl.nondet.exec_prompt = lambda *args, **kwargs: next(votes)
    def run_voting(leader, validator):
        leader_result = leader()
        assert validator(sdk.gl.vm.Return(leader_result)) is False
        return leader_result
    sdk.gl.vm.run_nondet_unsafe = run_voting
    c.assess("vote", "users-v1", BASE.replace("Whether account is active", "Whether this account is active"))
    assert c.get_receipt("vote").verdict == "COMPATIBLE"
