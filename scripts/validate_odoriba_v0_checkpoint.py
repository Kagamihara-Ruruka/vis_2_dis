#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_SCRIPT = REPO_ROOT / "scripts" / "odoriba_v0_checkpoint.ps1"

REQUIRED_FLAGS = {
    "pytest_passed": True,
    "fixture_validation_passed": True,
    "fixture_schema_validation_passed": True,
    "positive_smoke_passed": True,
    "negative_smoke_passed": True,
}
BOUNDARY_FLAGS = {
    "repo_rename": False,
    "cross_repo_integration": False,
    "core_changed": False,
    "smoke_script_changed": False,
}


def _load_checkpoint_payload() -> dict:
    env = os.environ.copy()
    if "PYTEST_CURRENT_TEST" in env and "ODORIBA_CHECKPOINT_RECURSION_GUARD" not in env:
        env["ODORIBA_CHECKPOINT_RECURSION_GUARD"] = "1"

    completed = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(CHECKPOINT_SCRIPT),
            "-Json",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"checkpoint script failed: exit {completed.returncode}")

    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("checkpoint -Json output is not valid JSON") from exc


def _assert_payload(payload: dict) -> None:
    assert payload.get("schema") == "odoriba_v0_checkpoint_v1", payload
    assert payload.get("status") == "passed", payload
    assert payload.get("checkpoint_passed") is True, payload

    for key, expected in REQUIRED_FLAGS.items():
        if payload.get(key) is not expected:
            raise AssertionError(f"{key} must be {expected}")

    for key, expected in BOUNDARY_FLAGS.items():
        if payload.get(key) is not expected:
            raise AssertionError(f"{key} must be {expected}")


def _negative_mutations(payload: dict) -> list[dict]:
    mutations: list[tuple[str, dict]] = []
    def _mutate_single(key: str, value: object) -> dict:
        baseline = copy.deepcopy(payload)
        baseline[key] = value
        return baseline

    mutations.append(("repo_rename=true", _mutate_single("repo_rename", True)))
    mutations.append(("cross_repo_integration=true", _mutate_single("cross_repo_integration", True)))
    mutations.append(("core_changed=true", _mutate_single("core_changed", True)))
    mutations.append(("smoke_script_changed=true", _mutate_single("smoke_script_changed", True)))

    for key in REQUIRED_FLAGS:
        mutations.append((f"{key}=False", _mutate_single(key, False)))

    bad_status = copy.deepcopy(payload)
    bad_status["checkpoint_passed"] = False
    bad_status["status"] = payload.get("status", "passed")
    mutations.append(("status=passed while checkpoint_passed=False", bad_status))

    return mutations


def _run_negative_self_test(payload: dict) -> list[str]:
    failures: list[str] = []
    # Start from valid payload to ensure mutation is the only cause.
    baseline = copy.deepcopy(payload)
    for label, mutated in _negative_mutations(baseline):
        try:
            _assert_payload(mutated)
        except AssertionError as err:
            continue
        failures.append(f"mutation undetected: {label}")
    return failures


def _load_payload_with_guard() -> dict:
    return _load_checkpoint_payload()


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Odoriba v0 checkpoint JSON output")
    parser.add_argument("--self-test-negative", action="store_true", help="run in-memory negative mutation checks")
    args = parser.parse_args()

    payload = _load_payload_with_guard()
    _assert_payload(payload)
    print("checkpoint payload validation passed")

    if args.self_test_negative:
        failures = _run_negative_self_test(payload)
        if failures:
            for item in failures:
                print(f"negative self-test failed: {item}")
            return 1
        print("negative self-test passed (mutations detected)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
