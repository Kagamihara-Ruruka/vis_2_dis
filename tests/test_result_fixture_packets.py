import json
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "odoriba_v0_result_packets"
SMOKE_SCRIPT = REPO_ROOT / "scripts" / "odoriba_v0_smoke.ps1"


def _load_fixtures():
    return sorted(FIXTURE_DIR.glob("*.json"))


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


@pytest.mark.parametrize("fixture_path", _load_fixtures(), ids=lambda p: Path(p).stem)
def test_result_fixture_packet_smoke_matrix(fixture_path: Path):
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))

    request_card = fixture["request_card"]
    expected_result = fixture["translation_result"]
    forbidden_request_fields = {"payload", "raw", "dataframe", "binary", "metadata"}
    assert not forbidden_request_fields.intersection(request_card.keys())
    assert fixture["mode"] in {"positive", "negative"}
    assert fixture["expected_status"] in {"success", "failed", "success_with_no_evidence"}

    proc = _run_smoke(fixture["mode"], fixture.get("smoke_translator_arg", request_card["requested_translator"]))
    assert proc.returncode == fixture["expected_exit_code"]

    if fixture["expected_smoke_ok"]:
        assert "SMOKE_OK" in proc.stdout
    else:
        assert "SMOKE_OK" not in proc.stdout

    result = _parse_smoke_json(proc.stdout, "result")

    assert result["status"] == fixture["expected_status"]
    assert result["boundary_scope"] == fixture["boundary_scope"]
    assert result["status"] == expected_result["status"]
    assert result["card_id"] == expected_result["card_id"]
    assert result["card_kind"] == expected_result["card_kind"]
    assert result["output_card_ref"] == expected_result["output_card_ref"]
    assert result["evidence_refs"] == expected_result["evidence_refs"]
    assert result["request_card_ref"] == expected_result["request_card_ref"]
    assert result["source_card_ref"] == expected_result["source_card_ref"]
    assert result["translator_id"] == expected_result["translator_id"]
    assert result["diagnostics"] == expected_result["diagnostics"]
    assert result["subject_ref"] == request_card["subject_ref"]
    assert result["source_card_ref"] == request_card["source_card_ref"]
    assert result["translator_id"] == request_card["requested_translator"]

    diagnostics = result.get("diagnostics", [])
    for fragment in fixture["expected_diagnostics_contains"]:
        assert any(fragment in item for item in diagnostics)

    if result["status"] == "success" and result["evidence_refs"] == []:
        assert any("mock prototype" in item.lower() for item in diagnostics)

    if result["status"] in {"failed"}:
        assert result["output_card_ref"] == ""
        assert any("Unknown translator" in item for item in diagnostics)
