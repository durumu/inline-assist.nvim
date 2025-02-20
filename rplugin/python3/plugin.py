from __future__ import annotations

import pynvim

from llm import stream_rewritten_lines
from structs.diagnostic import Diagnostic


def escape_quotes(s: str) -> str:
    return s.replace('"', r"\"")


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
            d for d in all_diagnostics if d.lnum < end_lnum and start_lnum < d.end_lnum
        ]

        rewrite_stream = stream_rewritten_lines(
            buf[:],
            (start_lnum, end_lnum),
            user_prompt,
            buf.options["filetype"],
            relevant_diagnostics,
        )

        buf[start_lnum:end_lnum] = ""
        for i, line in enumerate(rewrite_stream):
            insert_lnum = start_lnum + i
            # janky but it works!
            self.nvim.command(
                f'undojoin | lua vim.api.nvim_buf_set_lines(0, {insert_lnum}, {insert_lnum}, false, {{"{escape_quotes(line)}"}})'
            )
