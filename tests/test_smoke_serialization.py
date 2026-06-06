from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from rrkal_odoriba.cards import OperationRequestCard, ViewCard
from rrkal_odoriba.results import TranslationResultCard, TranslationResultStatus


def test_request_to_json_compatible_contains_required_fields() -> None:
    request = OperationRequestCard(
        card_id="smoke-req-001",
        card_kind="OperationRequestCard",
        schema_version="v0",
        producer="unit-test",
        subject_ref="asset:smoke-alpha",
        status="requested",
        source_card_ref="asset-card-001",
        operation="mock_translate",
        requested_view="summary",
        target_domain="smoke-domain",
        requested_translator="mock_view_v0",
    )

    payload = request.to_json_compatible_dict()

    assert isinstance(payload, dict)
    assert payload["card_id"] == "smoke-req-001"
    assert payload["card_kind"] == "OperationRequestCard"
    assert payload["producer"] == "unit-test"
    assert payload["subject_ref"] == "asset:smoke-alpha"
    assert isinstance(payload["evidence_refs"], list)
    assert payload["boundary_scope"] == "RRKAL_odoriba_reflex_arc_v0"


def test_result_to_json_compatible_contains_expected_shape() -> None:
    result = TranslationResultCard(
        card_id="smoke-req-001::result",
        card_kind="TranslationResultCard",
        schema_version="v0",
        producer="OdoribaCore",
        subject_ref="asset:smoke-alpha",
        status=TranslationResultStatus.SUCCESS,
        evidence_refs=("evidence-001",),
        request_card_ref="smoke-req-001",
        source_card_ref="asset-card-001",
        translator_id="mock_view_v0",
        output_card_ref="smoke-req-001::summary",
        diagnostics=("ok",),
    )
    payload = result.to_json_compatible_dict()

    assert isinstance(payload["diagnostics"], tuple)
    assert payload["diagnostics"] == ("ok",)
    assert payload["request_card_ref"] == "smoke-req-001"
    assert isinstance(payload["evidence_refs"], list)


def test_view_card_to_json_compatible_is_compatible() -> None:
    view = ViewCard(
        card_id="smoke-req-001::view",
        card_kind="ViewCard",
        schema_version="v0",
        producer="mock-translator",
        subject_ref="asset:smoke-alpha",
        status="translated",
        view_id="smoke-req-001::summary",
        target_domain="smoke-domain",
        view_kind="summary",
        source_card_ref="asset-card-001",
        hints=("h1", "h2"),
    )
    payload = view.to_json_compatible_dict()

    assert payload["card_kind"] == "ViewCard"
    assert isinstance(payload["hints"], tuple)


def _run_smoke(mode: str, translator: str) -> str:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "odoriba_v0_smoke.ps1"
    command = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script_path),
        "-Mode",
        mode,
        "-Translator",
        translator,
    ]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True,
    )
    if completed.stderr:
        print(completed.stderr, file=sys.stderr)
    return completed.stdout


def test_smoke_script_positive_mode() -> None:
    output = _run_smoke("positive", "mock_view_v0")
    assert "SMOKE_OK" in output
    lines = [
        line.split("=", 1)[1]
        for line in output.splitlines()
        if line.startswith("SMOKE_RESULT_JSON=")
    ]
    assert lines
    result_payload = json.loads(lines[0])
    assert result_payload["card_kind"] == "TranslationResultCard"


def test_smoke_script_positive_mode_rejects_unknown_translator() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "odoriba_v0_smoke.ps1"
    completed = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script_path),
            "-Mode",
            "positive",
            "-Translator",
            "o1_unknown_probe",
        ],
        capture_output=True,
        text=True,
    )
    combined = (completed.stdout or "") + (completed.stderr or "")
    assert completed.returncode != 0
    assert "SMOKE_OK" not in combined
    lines = [
        line.split("=", 1)[1]
        for line in completed.stdout.splitlines()
        if line.startswith("SMOKE_RESULT_JSON=")
    ]
    if lines:
        payload = json.loads(lines[0])
        assert payload["status"] == "failed"
        assert "Unknown translator" in "".join(payload["diagnostics"])


def test_smoke_script_negative_unknown_translator_rejected() -> None:
    output = _run_smoke("negative", "mock_view_v0")
    assert "SMOKE_OK" in output
    lines = [
        line.split("=", 1)[1]
        for line in output.splitlines()
        if line.startswith("SMOKE_RESULT_JSON=")
    ]
    assert lines
    result_payload = json.loads(lines[0])
    assert result_payload["status"] == "failed"
    assert "Unknown translator" in "".join(result_payload["diagnostics"])
