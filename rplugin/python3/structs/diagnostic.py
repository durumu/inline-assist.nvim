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
