def replace_code_includes_with_placeholders(text: list[str]) -> list[str]:
    """
    Replace code includes with placeholders.
    """

    modified_text = text.copy()
    includes = extract_code_includes(text)
    for include in includes:
        modified_text[include["line_no"] - 1] = CODE_INCLUDE_PLACEHOLDER
    return modified_text