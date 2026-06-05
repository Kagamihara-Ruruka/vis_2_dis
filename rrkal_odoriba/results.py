"""Result card definitions for the Odoriba minimal reflex arc mock."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .cards import CardBase


class TranslationResultStatus:
    SUCCESS = "success"
    SUCCESS_WITH_NO_EVIDENCE = "success_with_no_evidence"
    FAILED = "failed"


@dataclass(frozen=True)
class TranslationResultCard(CardBase):
    """Result card for a single mock translation attempt."""

    request_card_ref: str = ""
    source_card_ref: str = ""
    translator_id: str = ""
    output_card_ref: str = ""
    diagnostics: Tuple[str, ...] = ()
