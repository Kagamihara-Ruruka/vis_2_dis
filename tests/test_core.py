from __future__ import annotations

import pytest
from dataclasses import dataclass

from rrkal_odoriba.cards import OperationRequestCard
from rrkal_odoriba.core import OdoribaCore
from rrkal_odoriba.results import TranslationResultCard, TranslationResultStatus
from rrkal_odoriba.translators import MockTranslator, Translator
from rrkal_odoriba.cards import ViewCard


@dataclass(frozen=True)
class NoOpTranslator(Translator):
    translator_id: str = "noop_v0"

    def translate(self, request_card: OperationRequestCard) -> ViewCard:
        return ViewCard(
            card_id="noop::view",
            card_kind="ViewCard",
            schema_version=request_card.schema_version,
            producer="unit-test",
            subject_ref=request_card.subject_ref,
            status="translated",
            view_id="noop::view",
            target_domain=request_card.target_domain,
            view_kind=request_card.requested_view,
            source_card_ref=request_card.source_card_ref,
        )


def _build_request(translator_id: str, evidence_required: bool = False) -> OperationRequestCard:
    return OperationRequestCard(
        card_id="req-001",
        card_kind="OperationRequestCard",
        schema_version="v0",
        producer="unit-test",
        subject_ref="asset:alpha",
        status="requested",
        source_card_ref="asset-card-001",
        operation="mock_translate",
        requested_view="summary",
        target_domain="mock",
        requested_translator=translator_id,
        evidence_required=evidence_required,
    )


def test_handle_with_known_translator_produces_result() -> None:
    core = OdoribaCore((MockTranslator(), NoOpTranslator()))
    result = core.handle(_build_request("mock_view_v0"))
    assert isinstance(result, TranslationResultCard)
    assert result.status == TranslationResultStatus.SUCCESS
    assert result.translator_id == "mock_view_v0"
    assert result.output_card_ref.endswith("summary")
    assert result.source_card_ref == "asset-card-001"
    assert len(result.diagnostics) > 0


def test_handle_with_unknown_translator_fails() -> None:
    core = OdoribaCore((MockTranslator(),))
    result = core.handle(_build_request("unknown_v0"))
    assert result.status == TranslationResultStatus.FAILED
    assert result.output_card_ref == ""
    assert result.translator_id == "unknown_v0"
    assert any("Unknown translator" in item for item in result.diagnostics)


def test_no_evidence_reason_is_recorded_when_required() -> None:
    core = OdoribaCore((MockTranslator(),))
    result = core.handle(_build_request("mock_view_v0", evidence_required=True))
    assert result.status == TranslationResultStatus.SUCCESS_WITH_NO_EVIDENCE
    assert result.evidence_refs == ()
    assert any("No evidence refs were emitted" in item for item in result.diagnostics)
