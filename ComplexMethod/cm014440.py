def process_signature(line: str) -> list[str]:
    """
    Clean up a given raw function signature.

    This includes removing the self-referential datapipe argument, default
    arguments of input functions, newlines, and spaces.
    """
    tokens: list[str] = split_outside_bracket(line)
    for i, token in enumerate(tokens):
        tokens[i] = token.strip(" ")
        if token == "cls":
            tokens[i] = "self"
        elif i > 0 and ("self" == tokens[i - 1]) and (tokens[i][0] != "*"):
            # Remove the datapipe after 'self' or 'cls' unless it has '*'
            tokens[i] = ""
        elif "Callable =" in token:  # Remove default argument if it is a function
            head = token.rpartition("=")[0]
            tokens[i] = head.strip(" ") + " = ..."
    tokens = [t for t in tokens if t != ""]
    return tokens