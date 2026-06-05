"""Translator implementations for the Odoriba minimal reflex arc mock."""

from __future__ import annotations

from dataclasses import dataclass

from .cards import OperationRequestCard, ViewCard


@dataclass(frozen=True)
class Translator:
    """Base translator contract."""

    translator_id: str

    def translate(self, request_card: OperationRequestCard) -> ViewCard:
        raise NotImplementedError("Translator implementations must override translate().")


@dataclass(frozen=True)
class MockTranslator(Translator):
    """Simple translator stub for the first mock reflex arc."""

    translator_id: str = "mock_view_v0"

    def translate(self, request_card: OperationRequestCard) -> ViewCard:
        view_id = f"{request_card.card_id}::{request_card.requested_view}"
        return ViewCard(
            card_id=f"{request_card.card_id}::view",
            card_kind="ViewCard",
            schema_version=request_card.schema_version,
            producer="mock-translator",
            subject_ref=request_card.subject_ref,
            status="translated",
            evidence_refs=(),
            boundary_scope=request_card.boundary_scope,
            view_id=view_id,
            target_domain=request_card.target_domain,
            view_kind=request_card.requested_view,
            source_card_ref=request_card.source_card_ref,
            hints=(
                f"operation={request_card.operation}",
                f"requested_translator={self.translator_id}",
            ),
        )
