from __future__ import annotations

from rrkal_odoriba.cards import OperationRequestCard
from rrkal_odoriba.core import OdoribaCore
from rrkal_odoriba.results import TranslationResultStatus
from rrkal_odoriba.translators import MockTranslator


def _request(
    request_id: str = "req-001",
    *,
    translator_id: str = "mock_view_v0",
    evidence_required: bool = False,
) -> OperationRequestCard:
    return OperationRequestCard(
        card_id=request_id,
        card_kind="OperationRequestCard",
        schema_version="v0",
        producer="boundary-tests",
        subject_ref="asset:alpha",
        status="requested",
        source_card_ref="asset-card-001",
        operation="interpret",
        requested_view="summary",
        target_domain="mock",
        requested_translator=translator_id,
        evidence_required=evidence_required,
    )


def test_rejection_when_translator_not_registered() -> None:
    core = OdoribaCore((MockTranslator(),))
    result = core.handle(_request(translator_id="missing_v0"))
    assert result.card_kind == "TranslationResultCard"
    assert result.status == TranslationResultStatus.FAILED
    assert result.output_card_ref == ""
    assert result.translator_id == "missing_v0"
    assert any("Unknown translator" in item for item in result.diagnostics)


def test_request_card_has_no_payload_fields() -> None:
    request = _request()
    forbidden_keys = {"payload", "raw", "dataframe", "binary"}
    assert forbidden_keys.isdisjoint(request.__dict__.keys())


def test_empty_evidence_requires_diagnostics() -> None:
    core = OdoribaCore((MockTranslator(),))
    result = core.handle(_request(evidence_required=True))
    assert result.evidence_refs == ()
    assert len(result.diagnostics) > 0
    assert all(isinstance(item, str) for item in result.diagnostics)
    assert any("No evidence refs were emitted" in item for item in result.diagnostics)


def test_translator_result_traverses_core_to_view_reference() -> None:
    core = OdoribaCore((MockTranslator(),))
    result = core.handle(_request())
    assert result.source_card_ref == "asset-card-001"
    assert result.request_card_ref == "req-001"
    assert result.output_card_ref.endswith("summary")
    assert result.translator_id == "mock_view_v0"
