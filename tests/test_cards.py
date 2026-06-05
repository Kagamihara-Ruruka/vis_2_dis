from __future__ import annotations

from rrkal_odoriba.cards import CardBase, OperationRequestCard, ViewCard


def _build_base() -> CardBase:
    return CardBase(
        card_id="card-001",
        card_kind="CardBase",
        schema_version="v0",
        producer="unit-test",
        subject_ref="asset:alpha",
        status="created",
    )


def test_cardbase_to_dict_is_json_friendly() -> None:
    card = _build_base()
    payload = card.to_json_compatible_dict()
    assert payload["card_id"] == "card-001"
    assert isinstance(payload["evidence_refs"], list)
    assert payload["boundary_scope"] == "RRKAL_odoriba_reflex_arc_v0"


def test_request_and_view_cards_have_no_payload_slot() -> None:
    request = OperationRequestCard(
        card_id="req-001",
        card_kind="OperationRequestCard",
        schema_version="v0",
        producer="unit-test",
        subject_ref="asset:alpha",
        status="requested",
        source_card_ref="asset-card-001",
        operation="interpret",
        requested_view="summary",
        target_domain="mock",
        requested_translator="mock_view_v0",
    )
    view = ViewCard(
        card_id="view-001",
        card_kind="ViewCard",
        schema_version="v0",
        producer="mock-translator",
        subject_ref="asset:alpha",
        status="translated",
        view_id="view-001",
        target_domain="mock",
        view_kind="summary",
        source_card_ref="asset-card-001",
    )
    assert "payload" not in request.__dict__
    assert "payload" not in view.__dict__
    assert request.requested_translator == "mock_view_v0"
    assert request.evidence_required is False
