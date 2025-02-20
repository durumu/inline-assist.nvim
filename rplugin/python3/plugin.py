from __future__ import annotations

import pynvim

from llm import stream_rewritten_lines
from structs.diagnostic import Diagnostic


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

        all_diagnostics = [
            Diagnostic(**d) for d in self.nvim.exec_lua("return vim.diagnostic.get()")
        ]
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

        # Delete this to prepare for a rewrite.
        # TODO: We should really do some diffing
        buf[start_lnum:end_lnum] = ""

        fragments_starting_next_line = []
        current_lnum = start_lnum
        for chunk in rewrite_stream:
            # start_of_next_line is the empty string if chunk ends in a newline.
            *lines, start_of_next_line = chunk.split("\n")
            if lines:
                lines[0] = "".join([*fragments_starting_next_line, lines[0]])
                buf[current_lnum:current_lnum] = lines
                current_lnum += len(lines)
                fragments_starting_next_line = []
            fragments_starting_next_line.append(start_of_next_line)
