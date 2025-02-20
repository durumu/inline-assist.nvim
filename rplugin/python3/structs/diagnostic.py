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
        return cls(
            bufnr=nvim_diagnostic["bufnr"],
            lnum=nvim_diagnostic["lnum"],
            end_lnum=nvim_diagnostic["end_lnum"],
            col=nvim_diagnostic["col"],
            end_col=nvim_diagnostic["end_col"],
            severity=DiagnosticSeverity(nvim_diagnostic["severity"]),
            message=nvim_diagnostic["message"],
            source=nvim_diagnostic["source"],
            code=nvim_diagnostic.get("code"),
            user_data=nvim_diagnostic.get("user_data"),
            namespace=nvim_diagnostic.get("namespace"),
        )
