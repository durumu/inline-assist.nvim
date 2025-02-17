from __future__ import annotations
from typing import TYPE_CHECKING
from functools import cache

import pynvim

# from anthropic import Anthropic
# from prompting import make_rewrite_prompt

if TYPE_CHECKING:
    from pynvim.api import Buffer, Nvim


# @cache
# def anthropic_client():
#     return Anthropic()


def get_completion(
    buf: Buffer,
    rewrite_range: tuple[int, int],  # [start, end)
    user_prompt: str,
) -> list[str]:
    rewrite_start, rewrite_end = rewrite_range
    if rewrite_start == rewrite_end:
        return []

    # prompt = make_rewrite_prompt(
    #     document_lines=buf[:],
    #     rewrite_range=rewrite_range,
    #     user_prompt=user_prompt,
    #     filetype=buf.options["filetype"],
    # )

    # client = anthropic_client()
    # client.messages.create(
    #     model="claude-3-5-sonnet-latest",
    #     max_tokens=8192,
    #     messages=[
    #         {
    #             "role": "user",
    #             "content": {
    #                 "type": "text",
    #                 "text": prompt,
    #             },
    #         }
    #     ],
    # )
    # TODO fixme
    return ["One day this will be AI-generated"]


@pynvim.plugin
class InlineAssist:
    nvim: Nvim

    def __init__(self, nvim: Nvim) -> None:
        self.nvim = nvim

    @pynvim.command("Ai", nargs="*", range="")
    def ai_command(self, args: list[str], line_range: tuple[int, int] | None) -> None:
        buf = self.nvim.current.buffer

        if not line_range or line_range == (0, 0):
            # bleck, 1-indexed fully inclusive range?
            line_range = (1, len(buf))

        start_row, end_row = line_range
        # transform into 0-indexed half-open [start, end) range
        start_row -= 1

        selected_lines = buf[start_row:end_row]
        selected_text = "\n".join(selected_lines)

        user_prompt = " ".join(args)

        completion = get_completion(buf, (start_row, end_row), user_prompt)

        # Replace the selected text with the result for now
        # eventually let's have an actual dialog
        buf[start_row:end_row] = completion
