def replace_multiline_code_block(
    block_a: MultilineCodeBlockInfo, block_b: MultilineCodeBlockInfo
) -> list[str]:
    """
    Replace multiline code block `a` with block `b` leaving comments intact.

    Syntax of comments depends on the language of the code block.
    Raises ValueError if the blocks are not compatible (different languages or different number of lines).
    """

    start_line = block_a["start_line_no"]
    end_line_no = start_line + len(block_a["content"]) - 1

    if block_a["lang"] != block_b["lang"]:
        raise ValueError(
            f"Code block (lines {start_line}-{end_line_no}) "
            "has different language than the original block "
            f"('{block_a['lang']}' vs '{block_b['lang']}')"
        )
    if len(block_a["content"]) != len(block_b["content"]):
        raise ValueError(
            f"Code block (lines {start_line}-{end_line_no}) "
            "has different number of lines than the original block "
            f"({len(block_a['content'])} vs {len(block_b['content'])})"
        )

    block_language = block_a["lang"].lower()
    if block_language in {"mermaid"}:
        if block_a != block_b:
            print(
                f"Skipping mermaid code block replacement (lines {start_line}-{end_line_no}). "
                "This should be checked manually."
            )
        return block_a["content"].copy()  # We don't handle mermaid code blocks for now

    code_block: list[str] = []
    for line_a, line_b in zip(block_a["content"], block_b["content"], strict=False):
        line_a_comment: str | None = None
        line_b_comment: str | None = None

        # Handle comments based on language
        if block_language in {
            "python",
            "py",
            "sh",
            "bash",
            "dockerfile",
            "requirements",
            "gitignore",
            "toml",
            "yaml",
            "yml",
            "hash-style-comments",
        }:
            _line_a_code, line_a_comment = _split_hash_comment(line_a)
            _line_b_code, line_b_comment = _split_hash_comment(line_b)
            res_line = line_b
            if line_b_comment:
                res_line = res_line.replace(line_b_comment, line_a_comment, 1)
            code_block.append(res_line)
        elif block_language in {"console", "json", "slash-style-comments"}:
            _line_a_code, line_a_comment = _split_slashes_comment(line_a)
            _line_b_code, line_b_comment = _split_slashes_comment(line_b)
            res_line = line_b
            if line_b_comment:
                res_line = res_line.replace(line_b_comment, line_a_comment, 1)
            code_block.append(res_line)
        else:
            code_block.append(line_b)

    return code_block