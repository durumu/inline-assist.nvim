from __future__ import annotations

import pynvim

from diff import Operation, stream_diff
from llm import stream_rewritten_lines
from structs.diagnostic import Diagnostic


def escape_string(s: str) -> str:
    """
    Replace single backslashes with double backslashes,
    then quotes with escaped quotes.
    """
    return s.replace("\\", "\\\\").replace('"', r"\"")


def apply_operation(
    nvim: pynvim.Nvim, op: Operation, *, lnum: int, undojoin: bool
) -> None:
    """
    Equivalent of op.apply(nvim.current.buffer, lnum), except it supports joining undos.
    """
    prefix = "undojoin | " if undojoin else ""
    lnum_start = lnum + op.offset_start
    lnum_end = lnum + op.offset_end
    lines_lua_array = "".join([
        "{",
        ", ".join(f'"{escape_string(line)}"' for line in op.lines),
        "}",
    ])

    # 0 is hardcoded buffer number (means current buffer)
    # false disables strict_indexing (out of bounds indices should not error)
    nvim.command(
        f"{prefix}lua vim.api.nvim_buf_set_lines(0, {lnum_start}, {lnum_end}, false, {lines_lua_array})"
    )


@pynvim.plugin
class InlineAssist:
    nvim: pynvim.Nvim

    def __init__(self, nvim: pynvim.Nvim) -> None:
        self.nvim = nvim

    @pynvim.command("InlineAssist", nargs="*", range="")
    def inline_assist(
        self, args: list[str], line_range: tuple[int, int] | None
    ) -> None:
        buf = self.nvim.current.buffer

        # line_range is a 1-indexed fully inclusive range (bleh!)
        if not line_range or line_range == (0, 0):
            line_range = (1, len(buf))

        start_lnum, end_lnum = line_range
        # transform it into 0-indexed half-open [start, end) range
        start_lnum -= 1

        user_prompt = " ".join(args)

        all_diagnostics = list(
            map(
                Diagnostic.from_nvim_diagnostic,
                self.nvim.exec_lua("return vim.diagnostic.get()"),
            )
        )
        # The diagnostic's range is [lnum, end_lnum] (inclusive).
        relevant_diagnostics = [
            d
            for d in all_diagnostics
            if d.lnum <= end_lnum and start_lnum <= d.end_lnum
        ]

        rewrite_stream = stream_rewritten_lines(
            buf[:],
            (start_lnum, end_lnum),
            user_prompt,
            buf.options["filetype"],
            relevant_diagnostics,
        )

        for i, op in enumerate(stream_diff(buf[start_lnum:end_lnum], rewrite_stream)):
            apply_operation(self.nvim, op, lnum=start_lnum, undojoin=i != 0)
