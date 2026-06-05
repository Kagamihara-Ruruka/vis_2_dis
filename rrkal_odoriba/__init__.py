"""RRKAL Odoriba minimal reflex arc mock package."""

from .cards import CardBase, OperationRequestCard, ViewCard
from .core import OdoribaCore
from .results import TranslationResultCard
from .translators import MockTranslator, Translator

__all__ = [
    "CardBase",
    "OperationRequestCard",
    "ViewCard",
    "OdoribaCore",
    "TranslationResultCard",
    "Translator",
    "MockTranslator",
]

__version__ = "0.0.0"
