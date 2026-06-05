param(
    [string]$Translator = "mock_view_v0"
)

$ErrorActionPreference = "Stop"

Set-Location -Path (Split-Path -Parent $MyInvocation.MyCommand.Path)
$repoRoot = (Resolve-Path "..\")
Set-Location -Path $repoRoot

$env:PYTHONPATH = $repoRoot

$env:ODORIBA_SMOKE_TRANSLATOR = $Translator

$pythonTemplate = @'
import json

from rrkal_odoriba.cards import OperationRequestCard
from rrkal_odoriba.core import OdoribaCore
from rrkal_odoriba.translators import MockTranslator


def normalize_payload(payload: dict) -> dict:
    payload["evidence_refs"] = list(payload.get("evidence_refs", ()))
    for key in ("dispatch_constraints", "hints"):
        if key in payload:
            payload[key] = list(payload.get(key, ()))
    return payload


request_card = OperationRequestCard(
    card_id="smoke-req-001",
    card_kind="OperationRequestCard",
    schema_version="v0",
    producer="odoriba-smoke",
    subject_ref="asset:smoke-alpha",
    status="requested",
    source_card_ref="asset-card-smoke-001",
    operation="mock_translate",
    requested_view="summary",
    target_domain="smoke-domain",
    requested_translator="__ODORIBA_SMOKE_TRANSLATOR__",
    evidence_required=False,
)

core = OdoribaCore((MockTranslator(),))
result = core.handle(request_card)

request_payload = normalize_payload(request_card.to_json_compatible_dict())
result_payload = normalize_payload(result.to_json_compatible_dict())

assert request_payload["card_kind"] == "OperationRequestCard"
assert result_payload["card_kind"] == "TranslationResultCard"
assert result_payload["status"] in {"success", "success_with_no_evidence", "failed"}
assert isinstance(request_payload["evidence_refs"], list)
assert isinstance(result_payload["evidence_refs"], list)

request_json = json.dumps(request_payload, sort_keys=True, ensure_ascii=False)
result_json = json.dumps(result_payload, sort_keys=True, ensure_ascii=False)

print("SMOKE_REQUEST_JSON=" + request_json)
print("SMOKE_RESULT_JSON=" + result_json)
print("SMOKE_OK")
'@

$python = $pythonTemplate.Replace("__ODORIBA_SMOKE_TRANSLATOR__", $env:ODORIBA_SMOKE_TRANSLATOR)

$python | py -3 -B -c "import sys; exec(sys.stdin.read())"
