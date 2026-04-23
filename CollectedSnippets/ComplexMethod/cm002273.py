def _normalize_docstring_code_fences(raw_doc: str) -> str:
    """
    Normalise raw docstring text (including the r\"\"\"...\"\"\" delimiters).

    One fix is applied: a closing ``` is inserted before the final \"\"\" when
    a code block is still open (unclosed fence).  Detection of bare code blocks
    (without an 'Example:' heading) is handled by the updated _re_example_or_return
    pattern in auto_docstring.py, which now also splits at ``` lines.
    """
    lines = raw_doc.split("\n")
    result: list[str] = []
    in_code_block = False

    for line in lines:
        stripped = line.strip()
        indent = line[: len(line) - len(line.lstrip())]

        if not in_code_block and stripped.startswith("```"):
            in_code_block = True

        elif in_code_block and stripped == "```":
            in_code_block = False

        elif in_code_block and stripped.endswith('"""'):
            if not stripped.startswith("```"):
                # Unclosed fence – insert closing ``` before the triple-quote line
                result.append(f"{indent}```")
            in_code_block = False

        result.append(line)

    return "\n".join(result)