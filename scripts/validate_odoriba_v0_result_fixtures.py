#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "odoriba_v0_result_packets"
SMOKE_SCRIPT = REPO_ROOT / "scripts" / "odoriba_v0_smoke.ps1"


def _read_fixtures(fixture_dir: Path) -> list[Path]:
    return sorted(fixture_dir.glob("*.json"))


def _run_smoke(mode: str, translator: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(SMOKE_SCRIPT),
            "-Mode",
            mode,
            "-Translator",
            translator,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def _parse_smoke_json(output: str, key: str) -> dict:
    prefix = f"SMOKE_{key.upper()}_JSON="
    for line in output.splitlines():
        if line.startswith(prefix):
            return json.loads(line[len(prefix) :])
    raise AssertionError(f"missing {prefix} in smoke output")


def _assert_no_forbidden_request_fields(fixture_id: str, request_card: dict) -> None:
    forbidden_request_fields = {"payload", "raw", "dataframe", "binary", "metadata"}
    forbidden_hit = forbidden_request_fields.intersection(request_card.keys())
    if forbidden_hit:
        raise AssertionError(
            f"{fixture_id}: request_card contains forbidden fields: {sorted(forbidden_hit)}"
        )


def _validate_fixture_shape(fixture: dict) -> list[str]:
    fixture_id = fixture.get("fixture_id", "<missing fixture_id>")
    errors: list[str] = []

    if "schema" not in fixture:
        errors.append(f"{fixture_id}: missing schema")
    if "fixture_id" not in fixture:
        errors.append(f"{fixture_id}: missing fixture_id")
    if fixture.get("mode") not in {"positive", "negative"}:
        errors.append(f"{fixture_id}: mode must be positive or negative")
    if fixture.get("verified") is not False:
        errors.append(f"{fixture_id}: verified must be false in v0 mock prototype")

    request_card = fixture.get("request_card")
    if not isinstance(request_card, dict):
        errors.append(f"{fixture_id}: request_card must be an object")
        return errors

    request_card_forbidden_fields = {"payload", "raw", "dataframe", "binary", "metadata"}
    if request_card_forbidden_fields.intersection(request_card.keys()):
        errors.append(
            f"{fixture_id}: request_card contains forbidden fields: "
            f"{sorted(request_card_forbidden_fields.intersection(request_card.keys()))}"
        )

    translation_result = fixture.get("translation_result")
    if not isinstance(translation_result, dict):
        errors.append(f"{fixture_id}: translation_result must be an object")
        return errors

    if "evidence_refs" not in translation_result:
        errors.append(f"{fixture_id}: translation_result missing evidence_refs")
    if "diagnostics" not in translation_result:
        errors.append(f"{fixture_id}: translation_result missing diagnostics")
    if not isinstance(translation_result.get("diagnostics"), list):
        errors.append(f"{fixture_id}: translation_result.diagnostics must be a list")

    if fixture.get("mode") == "negative":
        smoke_arg = fixture.get("smoke_translator_arg", request_card.get("requested_translator"))
        requested = request_card.get("requested_translator")
        if not smoke_arg or smoke_arg == requested:
            errors.append(
                f"{fixture_id}: negative fixture requires smoke_translator_arg != request_card.requested_translator"
            )
        if requested and "unknown_unknown_" in requested:
            errors.append(f"{fixture_id}: requested_translator should not be unknown_unknown_*")

    for bad in ("unknown_unknown_",):
        for key in ("requested_translator",):
            candidate = request_card.get(key)
            if isinstance(candidate, str) and bad in candidate:
                errors.append(f"{fixture_id}: request_card.{key} contains forbidden {bad}")
        candidate = translation_result.get("translator_id")
        if isinstance(candidate, str) and bad in candidate:
            errors.append(f"{fixture_id}: translation_result.translator_id contains forbidden {bad}")

    return errors


def _collect_smoke_invariants(fixture_path: Path) -> None:
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    fixture_id = fixture.get("fixture_id", fixture_path.name)
    errors = _validate_fixture_shape(fixture)
    if errors:
        raise AssertionError("\n".join(errors))

    request_card = fixture["request_card"]
    expected_result = fixture["translation_result"]
    mode = fixture["mode"]
    expected_status = fixture["expected_status"]
    expected_exit_code = fixture["expected_exit_code"]
    expected_smoke_ok = fixture["expected_smoke_ok"]

    smoke_arg = fixture.get("smoke_translator_arg", request_card["requested_translator"])
    proc = _run_smoke(mode, smoke_arg)
    if proc.returncode != expected_exit_code:
        raise AssertionError(
            f"{fixture_id}: smoke exit {proc.returncode} != expected {expected_exit_code}"
        )

    if expected_smoke_ok and "SMOKE_OK" not in proc.stdout:
        raise AssertionError(f"{fixture_id}: expected SMOKE_OK not present")
    if not expected_smoke_ok and "SMOKE_OK" in proc.stdout:
        raise AssertionError(f"{fixture_id}: expected no SMOKE_OK")

    result = _parse_smoke_json(proc.stdout, "result")

    if result["status"] != expected_status:
        raise AssertionError(
            f"{fixture_id}: status mismatch: expected {expected_status} / got {result['status']}"
        )
    if result["boundary_scope"] != fixture["boundary_scope"]:
        raise AssertionError(
            f"{fixture_id}: boundary_scope mismatch: "
            f"{result['boundary_scope']} != {fixture['boundary_scope']}"
        )
    if result["status"] == "success":
        if result.get("output_card_ref") != expected_result["output_card_ref"]:
            raise AssertionError(f"{fixture_id}: output_card_ref mismatch")
        if not result["evidence_refs"]:
            if not any("mock prototype" in item.lower() for item in result.get("diagnostics", [])):
                raise AssertionError(
                    f"{fixture_id}: empty evidence_refs requires mock prototype diagnostics"
                )
    else:
        if result.get("output_card_ref") != expected_result.get("output_card_ref", ""):
            raise AssertionError(f"{fixture_id}: failed output_card_ref mismatch")

    for field in (
        "card_id",
        "card_kind",
        "output_card_ref",
        "request_card_ref",
        "source_card_ref",
        "translator_id",
        "evidence_refs",
        "diagnostics",
    ):
        if result.get(field) != expected_result[field]:
            raise AssertionError(
                f"{fixture_id}: translation_result field mismatch on {field}: "
                f"{result.get(field)!r} != {expected_result[field]!r}"
            )

    if result["status"] != "success":
        if not any("Unknown translator" in item for item in result.get("diagnostics", [])):
            raise AssertionError(f"{fixture_id}: failed path missing unknown-translator diagnostics")


def _collect_smoke_only(fixture_paths: Iterable[Path]) -> None:
    for path in fixture_paths:
        _collect_smoke_invariants(path)


def _collect_schema_only(fixture_paths: Iterable[Path]) -> None:
    for path in fixture_paths:
        fixture = json.loads(path.read_text(encoding="utf-8"))
        fixture_id = fixture.get("fixture_id", path.name)
        errors = _validate_fixture_shape(fixture)
        if errors:
            raise AssertionError(f"{fixture_id}: " + "; ".join(errors))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Odoriba v0 result fixture packets"
    )
    parser.add_argument(
        "mode",
        nargs="?",
        choices=["schema", "smoke"],
        default="smoke",
        help="Validate fixture JSON shape only or execute smoke script.",
    )
    parser.add_argument(
        "--fixture-dir",
        default=str(FIXTURE_DIR),
        help="Fixture folder path",
    )
    args = parser.parse_args()

    fixture_paths = _read_fixtures(Path(args.fixture_dir))
    if not fixture_paths:
        print("No fixture files found.")
        return 1

    if args.mode == "schema":
        _collect_schema_only(fixture_paths)
    else:
        _collect_smoke_only(fixture_paths)

    print(f"Validated {len(fixture_paths)} fixture packet(s) with mode={args.mode}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
