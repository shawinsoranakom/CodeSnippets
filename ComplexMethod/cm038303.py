def make_valid_python(text: str) -> tuple[str, str] | None:
    """Attempt to close all open brackets/quotes to make partial Python valid.

    Used during streaming to parse incomplete tool call expressions by
    appending the necessary closing characters.

    Returns:
        A tuple of (completed_text, added_suffix) if the text can be
        made valid, or None if the text is too incomplete to complete
        meaningfully (e.g. mid-parameter-name or mid-dict-key).

    Raises:
        UnexpectedAstError: If mismatched brackets or parentheses
            are detected.
    """
    bracket_stack: list[str] = []
    for index, char in enumerate(text):
        if char in {"[", "(", "{"}:
            bracket_stack.append(char)
        elif char == "]":
            if not bracket_stack or bracket_stack.pop() != "[":
                raise UnexpectedAstError("Mismatched square brackets")
        elif char == ")":
            if not bracket_stack or bracket_stack.pop() != "(":
                raise UnexpectedAstError("Mismatched parentheses")
        elif char == "}":
            if not bracket_stack or bracket_stack.pop() != "{":
                raise UnexpectedAstError("Mismatched curly braces")
        elif char in {"'", '"'}:
            if bracket_stack and bracket_stack[-1] == char:
                if index > 0 and text[index - 1] == "\\":
                    pass
                else:
                    bracket_stack.pop()
            elif bracket_stack and bracket_stack[-1] in {"'", '"'}:
                pass
            else:
                bracket_stack.append(char)

    text = text.rstrip()
    if text.endswith("=") or text.endswith(":"):
        return None
    if bracket_stack and bracket_stack[-1] == "{":
        trailing_dict_text = text[: text.rfind("{")]
        num_keys = trailing_dict_text.count(":")
        num_values = trailing_dict_text.count(",")
        if num_keys <= num_values:
            return None
    if bracket_stack and bracket_stack[-1] == "(":
        trailing_params_text = text[: text.rfind("(")]
        num_full_param_names = trailing_params_text.count("=")
        num_full_param_values = trailing_params_text.count(",")
        if num_full_param_names <= num_full_param_values:
            return None
    if text.endswith(","):
        text = text[:-1]
    if (
        bracket_stack
        and bracket_stack[-1] == "["
        and not text.endswith("[")
        and not text.endswith(")")
    ):
        return None

    _CLOSING = {"[": "]", "(": ")", "{": "}", "'": "'", '"': '"'}
    added_text = ""
    for char in reversed(bracket_stack):
        added_text += _CLOSING[char]

    return text + added_text, added_text