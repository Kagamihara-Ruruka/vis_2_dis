"""Card definitions for the Odoriba minimal reflex arc mock."""

from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Tuple


@dataclass(frozen=True)
class CardBase:
    """Common base for all mock cards."""

    card_id: str
    card_kind: str
    schema_version: str
    producer: str
    subject_ref: str
    status: str
    evidence_refs: Tuple[str, ...] = field(default_factory=tuple)
    boundary_scope: str = "RRKAL_odoriba_reflex_arc_v0"

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json_compatible_dict(self) -> dict:
        data = self.to_dict()
        data["evidence_refs"] = list(self.evidence_refs)
        return data

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(card_id={self.card_id!r}, card_kind={self.card_kind!r}, status={self.status!r})"

    __str__ = __repr__


@dataclass(frozen=True)
class OperationRequestCard(CardBase):
    """Operation request card for mock translation dispatch."""

    source_card_ref: str = ""
    operation: str = ""
    requested_view: str = "default"
    target_domain: str = "default"
    requested_translator: str = ""
    dispatch_constraints: Tuple[str, ...] = field(default_factory=tuple)
    evidence_required: bool = False


@dataclass(frozen=True)
class ViewCard(CardBase):
    """View card produced by the mock translator."""

    view_id: str = ""
    target_domain: str = "default"
    view_kind: str = "default"
    source_card_ref: str = ""
    hints: Tuple[str, ...] = field(default_factory=tuple)
