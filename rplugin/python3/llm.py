from __future__ import annotations

import textwrap
from functools import cache

import anthropic

from structs.diagnostic import Diagnostic


@cache
def anthropic_client():
    # TODO: async?
    return anthropic.Anthropic()


def get_rewrite(
    document_lines: list[str],
    rewrite_range: tuple[int, int],  # [start, end)
    user_prompt: str,
    filetype: str,
    diagnostics: list[Diagnostic],
) -> list[str]:
    rewrite_start, rewrite_end = rewrite_range
    if rewrite_start == rewrite_end:
        return []

    prompt = _make_rewrite_prompt(
        document_lines=document_lines,
        rewrite_range=rewrite_range,
        user_prompt=user_prompt,
        filetype=filetype,
        diagnostics=diagnostics,
    )

    message = anthropic_client().messages.create(
        model="claude-3-5-sonnet-latest",
        max_tokens=8192,
        messages=[
            {"role": "user", "content": prompt},
            # We force the assistant to behave according to the prompt by prefilling
            # the start XML tag.
            # todo: maybe try out giving the assistant the ability to think first?
            {"role": "assistant", "content": "<rewritten>"},
        ],
    )

    (block,) = message.content
    assert isinstance(block, anthropic.types.text_block.TextBlock)
    lines = block.text.strip().split("\n")
    # todo: maybe do something nicer with the error?
    assert lines[-1] == "</rewritten>", "bad rewrite"
    return lines[:-1]


def _make_rewrite_prompt(
    *,
    document_lines: list[str],
    rewrite_range: tuple[int, int],  # [start, end)
    user_prompt: str,
    filetype: str | None,
    diagnostics: list[Diagnostic],
) -> str:
    filetype = filetype or "text"
    content_type = "text" if filetype == "text" else "code"

    if rewrite_range == (0, len(document_lines)):
        # Full file case -- no need for rewrite markers.
        return textwrap.dedent(
            f"""
            Here's a file of {filetype} that I'm going to ask you to make an edit to.

            <document>
            {"\n".join(document_lines)}
            </document>

            Rewrite this document based on the following prompt:
            <prompt>
            {user_prompt}
            </prompt>

            Only make changes that are necessary to fulfill the prompt, leave everything else as is.

            Immediately start with the following format with no remarks. Enclose the exact {content_type} you are rewriting within <rewritten></rewritten>, as follows:

            <rewritten>
            {{REWRITTEN_{content_type.upper()}}}
            </rewritten>
            """
        )

    rewrite_start, rewrite_end = rewrite_range

    pre_rewrite = "\n".join(document_lines[:rewrite_start])
    rewrite = "\n".join(document_lines[rewrite_start:rewrite_end])
    post_rewrite = "\n".join(document_lines[rewrite_end:])

    if diagnostics:
        diagnostic_descriptions = [
            textwrap.dedent(
                f"""
                <diagnostic_error>
                <line_number>{diagnostic.lnum}</line_number>
                <error_message>
                {diagnostic.message}
                </error_message>
                <source_code>
                {diagnostic.source}
                </source_code>
                </diagnostic_error>
                """
            )
            for diagnostic in diagnostics
        ]

        diagnostic_prompt = textwrap.dedent(
            f"""
            Below are the diagnostic errors visible to the user. If the user requests problems to be fixed, use this information, but do not try to fix these errors if the user hasn't asked you to.

            {"\n\n".join(diagnostic_descriptions)}
            """
        )
    else:
        diagnostic_prompt = ""

    return textwrap.dedent(
        f"""
        Here's a file of {filetype} that I'm going to ask you to make an edit to.

        The section you'll need to rewrite is marked with <rewrite_this></rewrite_this> tags.

        <document>
        {pre_rewrite}
        <rewrite_this>
        {rewrite}
        </rewrite_this>
        {post_rewrite}
        </document>

        Edit the section of {content_type} in <rewrite_this></rewrite_this> tags based on the following prompt:
        <prompt>
        {user_prompt}
        </prompt>

        And here's the section to rewrite based on that prompt again for reference:
        <rewrite_this>
        {rewrite}
        </rewrite_this>

        {diagnostic_prompt}

        Only make changes that are necessary to fulfill the prompt, leave everything else as is. All surrounding {content_type} will be preserved.

        Start at the indentation level in the original file in the rewritten {content_type}. Don't stop until you've rewritten the entire section, even if you have no more changes to make, always write out the whole section with no unnecessary elisions.

        Immediately start with the following format with no remarks. Enclose the exact {content_type} you are rewriting within <rewritten></rewritten>, as follows:

        <rewritten>
        {{REWRITTEN_{content_type.upper()}}}
        </rewritten>
        """
    )
