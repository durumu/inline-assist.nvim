from __future__ import annotations

from functools import cache
from typing import TYPE_CHECKING

import anthropic
import pynvim
from prompting import make_rewrite_prompt

if TYPE_CHECKING:
    from pynvim.api import Buffer, Nvim


@cache
def anthropic_client():
    # TODO: async?
    return anthropic.Anthropic()


def get_completion(
    buf: Buffer,
    rewrite_range: tuple[int, int],  # [start, end)
    user_prompt: str,
) -> list[str]:
    rewrite_start, rewrite_end = rewrite_range
    if rewrite_start == rewrite_end:
        return []

    prompt = make_rewrite_prompt(
        document_lines=buf[:],
        rewrite_range=rewrite_range,
        user_prompt=user_prompt,
        filetype=buf.options["filetype"],
    )

    message = anthropic_client().messages.create(
        model="claude-3-5-sonnet-latest",
        max_tokens=8192,
        messages=[
            {"role": "user", "content": prompt},
            # todo: maybe try out giving the assistant the ability to think?
            {"role": "assistant", "content": "<rewritten>"},
        ],
    )

    (block,) = message.content
    assert isinstance(block, anthropic.types.text_block.TextBlock)
    lines = block.text.strip().split("\n")
    # todo: maybe do something nicer with the error?
    assert lines[-1] == "</rewritten>", "bad completion"
    return lines[:-1]


@pynvim.plugin
class InlineAssist:
    nvim: Nvim

    def __init__(self, nvim: Nvim) -> None:
        self.nvim = nvim

    @pynvim.command("InlineAssist", nargs="*", range="")
    def inline_assist(
        self, args: list[str], line_range: tuple[int, int] | None
    ) -> None:
        buf = self.nvim.current.buffer

        # line_range is a 1-indexed fully inclusive range
        if not line_range or line_range == (0, 0):
            line_range = (1, len(buf))

        start_row, end_row = line_range
        # transform it into 0-indexed half-open [start, end) range
        start_row -= 1

        user_prompt = " ".join(args)

        completion = get_completion(buf, (start_row, end_row), user_prompt)

        # Replace the selected text with the result for now
        # eventually let's have an actual dialog
        buf[start_row:end_row] = completion
