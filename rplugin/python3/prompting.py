import textwrap


def make_rewrite_prompt(
    *,
    document_lines: list[str],
    rewrite_range: tuple[int, int],  # [start, end)
    user_prompt: str,
    filetype: str | None,
):
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

            Immediately start with the following format with no remarks:

            ```
            {{REWRITTEN_{content_type.upper()}}}
            ```
            """
        )

    rewrite_start, rewrite_end = rewrite_range

    pre_rewrite = "\n".join(document_lines[:rewrite_start])
    rewrite = "\n".join(document_lines[rewrite_start:rewrite_end])
    post_rewrite = "\n".join(document_lines[rewrite_end:])

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

        Only make changes that are necessary to fulfill the prompt, leave everything else as is. All surrounding {content_type} will be preserved.

        Start at the indentation level in the original file in the rewritten {content_type}. Don't stop until you've rewritten the entire section, even if you have no more changes to make, always write out the whole section with no unnecessary elisions.

        Immediately start with the following format with no remarks:

        ```
        {{REWRITTEN_{content_type.upper()}}}
        ```
        """
    )
