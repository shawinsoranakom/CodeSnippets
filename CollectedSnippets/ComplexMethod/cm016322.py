def bracket_pairs(tokens: Sequence[TokenInfo]) -> dict[int, int]:
    """Returns a dictionary mapping opening to closing brackets"""
    braces: dict[int, int] = {}
    stack: list[int] = []
    in_fstring = False

    for i, t in enumerate(tokens):
        if t.type == token.OP and not in_fstring:
            if t.string in BRACKETS:
                stack.append(i)
            elif inv := BRACKETS_INV.get(t.string):
                if not stack:
                    raise ParseError(t, "Never opened")
                begin = stack.pop()

                if not (stack and stack[-1] == FSTRING_START):
                    braces[begin] = i

                b = tokens[begin].string
                if b != inv:
                    raise ParseError(t, f"Mismatched braces '{b}' at {begin}")
        elif t.type == FSTRING_START:
            stack.append(FSTRING_START)
            in_fstring = True
        elif t.type == FSTRING_END:
            if stack.pop() != FSTRING_START:
                raise ParseError(t, "Mismatched FSTRING_START/FSTRING_END")
            in_fstring = False
    if stack:
        raise ParseError(t, "Left open")
    return braces