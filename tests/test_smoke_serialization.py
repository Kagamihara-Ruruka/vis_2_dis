from __future__ import annotations

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
