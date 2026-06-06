import copy
import os
import subprocess
from pathlib import Path

from scripts.validate_odoriba_v0_checkpoint import (
    _assert_payload,
    _negative_mutations,
    _run_negative_self_test,
)


def test_checkpoint_payload_validation_accepts_valid_payload() -> None:
    payload = {
        "schema": "odoriba_v0_checkpoint_v1",
        "status": "passed",
        "checkpoint_passed": True,
        "pytest_passed": True,
        "fixture_validation_passed": True,
        "fixture_schema_validation_passed": True,
        "positive_smoke_passed": True,
        "negative_smoke_passed": True,
        "repo_rename": False,
        "cross_repo_integration": False,
        "core_changed": False,
        "smoke_script_changed": False,
    }
    _assert_payload(payload)


def test_checkpoint_validator_negative_mutation_detector_flags_violations() -> None:
    payload = {
        "schema": "odoriba_v0_checkpoint_v1",
        "status": "passed",
        "checkpoint_passed": True,
        "pytest_passed": True,
        "fixture_validation_passed": True,
        "fixture_schema_validation_passed": True,
        "positive_smoke_passed": True,
        "negative_smoke_passed": True,
        "repo_rename": False,
        "cross_repo_integration": False,
        "core_changed": False,
        "smoke_script_changed": False,
    }
    failures = _run_negative_self_test(copy.deepcopy(payload))
    assert failures == []


def test_validator_script_runs_and_reports_negative_self_test() -> None:
    script_path = (
        Path(__file__).resolve().parents[1] / "scripts" / "validate_odoriba_v0_checkpoint.py"
    )
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")

    completed = subprocess.run(
        ["py", "-3", "-B", str(script_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        check=False,
    )
    assert completed.returncode == 0
    assert "checkpoint payload validation passed" in completed.stdout

    completed_negative = subprocess.run(
        ["py", "-3", "-B", str(script_path), "--self-test-negative"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        check=False,
    )
    assert completed_negative.returncode == 0
    assert "negative self-test passed (mutations detected)" in completed_negative.stdout


def test_negative_mutations_are_single_field_fidelity_preserved() -> None:
    payload = {
        "schema": "odoriba_v0_checkpoint_v1",
        "status": "passed",
        "checkpoint_passed": True,
        "pytest_passed": True,
        "fixture_validation_passed": True,
        "fixture_schema_validation_passed": True,
        "positive_smoke_passed": True,
        "negative_smoke_passed": True,
        "repo_rename": False,
        "cross_repo_integration": False,
        "core_changed": False,
        "smoke_script_changed": False,
    }

    mutations = _negative_mutations(payload)
    assert mutations, "expected at least one mutation"

    for label, mutated in mutations:
        _assert_payload(payload)

        changed = [k for k in payload if mutated.get(k) != payload[k]]
        assert len(changed) == 1, f"{label}: non-single-field mutation: {changed}"

        changed_field = changed[0]
        for key in payload:
            if key == changed_field:
                continue
            assert mutated[key] == payload[key], f"{label}: {key} should be preserved"

        for required in (
            "schema",
            "status",
            "checkpoint_passed",
            "pytest_passed",
            "fixture_validation_passed",
            "fixture_schema_validation_passed",
            "positive_smoke_passed",
            "negative_smoke_passed",
            "repo_rename",
            "cross_repo_integration",
            "core_changed",
            "smoke_script_changed",
        ):
            if required != changed_field:
                assert mutated[required] == payload[required], f"{label}: {required} changed unexpectedly"
