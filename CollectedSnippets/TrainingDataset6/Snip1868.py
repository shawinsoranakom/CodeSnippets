def replace_placeholders_with_code_includes(
    text: list[str], original_includes: list[CodeIncludeInfo]
) -> list[str]:
    """
    Replace code includes placeholders with actual code includes from the original (English) document.
    Fail if the number of placeholders does not match the number of original includes.
    """

    code_include_lines = [
        line_no
        for line_no, line in enumerate(text)
        if line.strip() == CODE_INCLUDE_PLACEHOLDER
    ]

    if len(code_include_lines) != len(original_includes):
        raise ValueError(
            "Number of code include placeholders does not match the number of code includes "
            "in the original document "
            f"({len(code_include_lines)} vs {len(original_includes)})"
        )

    modified_text = text.copy()
    for i, line_no in enumerate(code_include_lines):
        modified_text[line_no] = original_includes[i]["line"]

    return modified_text