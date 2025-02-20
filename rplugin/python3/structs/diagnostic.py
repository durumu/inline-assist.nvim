from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Any


class DiagnosticSeverity(IntEnum):
    ERROR = 1
    WARN = 2
    INFO = 3
    HINT = 4


@dataclass
class Diagnostic:
    bufnr: int
    lnum: int
    end_lnum: int
    col: int
    end_col: int
    severity: DiagnosticSeverity
    message: str
    source: str
    code: str | int | None = None
    user_data: Any | None = None
    namespace: int | None = None

    @classmethod
    def from_nvim_diagnostic(cls, nvim_diagnostic: dict[str, Any]) -> Diagnostic:
        fields = {
            field.name: field.type for field in Diagnostic.__dataclass_fields__.values()
        }
        kwargs = {}
        for field_name, field_type in fields.items():
            value = nvim_diagnostic[field_name]
            if field_type == DiagnosticSeverity:
                value = DiagnosticSeverity(value)
            kwargs[field_name] = value
        return Diagnostic(**kwargs)
