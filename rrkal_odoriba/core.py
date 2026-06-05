"""OdoribaCore for mock reflex-arc dispatch."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Tuple

from .cards import OperationRequestCard
from .results import TranslationResultCard, TranslationResultStatus
from .translators import MockTranslator, Translator


@dataclass(frozen=True)
class OdoribaCore:
    """Mock dispatcher that runs mock translators over request cards."""

    translator_registry: Tuple[Translator, ...] = (MockTranslator(),)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "_registry",
            {translator.translator_id: translator for translator in self.translator_registry},
        )

    @property
    def translators(self) -> Mapping[str, Translator]:
        return dict(self._registry)

    def register_translator(self, translator: Translator) -> None:
        self._registry[translator.translator_id] = translator

    def handle(self, request_card: OperationRequestCard) -> TranslationResultCard:
        if request_card.card_kind != "OperationRequestCard":
            return TranslationResultCard(
                card_id=f"{request_card.card_id}::result",
                card_kind="TranslationResultCard",
                schema_version=request_card.schema_version,
                producer="OdoribaCore",
                subject_ref=request_card.subject_ref,
                status=TranslationResultStatus.FAILED,
                evidence_refs=(),
                boundary_scope=request_card.boundary_scope,
                request_card_ref=request_card.card_id,
                source_card_ref=request_card.source_card_ref,
                translator_id="",
                output_card_ref="",
                diagnostics=("Invalid card_kind; expected OperationRequestCard.",),
            )

        if not request_card.requested_translator:
            return TranslationResultCard(
                card_id=f"{request_card.card_id}::result",
                card_kind="TranslationResultCard",
                schema_version=request_card.schema_version,
                producer="OdoribaCore",
                subject_ref=request_card.subject_ref,
                status=TranslationResultStatus.FAILED,
                evidence_refs=(),
                boundary_scope=request_card.boundary_scope,
                request_card_ref=request_card.card_id,
                source_card_ref=request_card.source_card_ref,
                translator_id="",
                output_card_ref="",
                diagnostics=("No requested_translator provided; this prototype expects explicit translator dispatch.",),
            )

        translator = self._registry.get(request_card.requested_translator)
        if translator is None:
            return TranslationResultCard(
                card_id=f"{request_card.card_id}::result",
                card_kind="TranslationResultCard",
                schema_version=request_card.schema_version,
                producer="OdoribaCore",
                subject_ref=request_card.subject_ref,
                status=TranslationResultStatus.FAILED,
                evidence_refs=(),
                boundary_scope=request_card.boundary_scope,
                request_card_ref=request_card.card_id,
                source_card_ref=request_card.source_card_ref,
                translator_id=request_card.requested_translator,
                output_card_ref="",
                diagnostics=(f"Unknown translator: {request_card.requested_translator}",),
            )

        try:
            view_card = translator.translate(request_card)
        except Exception as exc:  # pragma: no cover - defensive path
            return TranslationResultCard(
                card_id=f"{request_card.card_id}::result",
                card_kind="TranslationResultCard",
                schema_version=request_card.schema_version,
                producer="OdoribaCore",
                subject_ref=request_card.subject_ref,
                status=TranslationResultStatus.FAILED,
                evidence_refs=(),
                boundary_scope=request_card.boundary_scope,
                request_card_ref=request_card.card_id,
                source_card_ref=request_card.source_card_ref,
                translator_id=request_card.requested_translator,
                output_card_ref="",
                diagnostics=(f"Translator execution failed: {exc}",),
            )

        evidence_refs: Tuple[str, ...] = ()
        diagnostics = list[str]()
        diagnostics.append(f"Translator {request_card.requested_translator} completed.")
        if not evidence_refs:
            diagnostics.append(
                "No evidence refs were emitted because this is a mock prototype translator."
            )

        status = (
            TranslationResultStatus.SUCCESS
            if not request_card.evidence_required
            else TranslationResultStatus.SUCCESS_WITH_NO_EVIDENCE
        )
        if request_card.evidence_required is False and not evidence_refs:
            diagnostics.append("Mock output accepted without evidence references.")

        return TranslationResultCard(
            card_id=f"{request_card.card_id}::result",
            card_kind="TranslationResultCard",
            schema_version=request_card.schema_version,
            producer="OdoribaCore",
            subject_ref=request_card.subject_ref,
            status=status,
            evidence_refs=evidence_refs,
            boundary_scope=request_card.boundary_scope,
            request_card_ref=request_card.card_id,
            source_card_ref=request_card.source_card_ref,
            translator_id=request_card.requested_translator,
            output_card_ref=view_card.view_id,
            diagnostics=tuple(diagnostics),
        )
