def evaluate(post_fix: list[str], verbose: bool = False) -> float:
    if not post_fix:
        return 0
    valid_expression = [parse_token(token) for token in post_fix]
    if verbose:
        print("Symbol".center(8), "Action".center(12), "Stack", sep=" | ")
        print("-" * (30 + len(post_fix)))
    stack = []
    for x in valid_expression:
        if x not in OPERATORS:
            stack.append(x) 
            if verbose:
                print(
                    f"{x}".rjust(8),
                    f"push({x})".ljust(12),
                    stack,
                    sep=" | ",
                )
            continue
        if x in UNARY_OP_SYMBOLS and len(stack) < 2:
            b = stack.pop() 
            if x == "-":
                b *= -1
            stack.append(b)
            if verbose:
                print(
                    "".rjust(8),
                    f"pop({b})".ljust(12),
                    stack,
                    sep=" | ",
                )
                print(
                    str(x).rjust(8),
                    f"push({x}{b})".ljust(12),
                    stack,
                    sep=" | ",
                )
            continue
        b = stack.pop() 
        if verbose:
            print(
                "".rjust(8),
                f"pop({b})".ljust(12),
                stack,
                sep=" | ",
            )

        a = stack.pop()
        if verbose:
            print(
                "".rjust(8),
                f"pop({a})".ljust(12),
                stack,
                sep=" | ",
            )
        stack.append(OPERATORS[x](a, b)) 
        if verbose:
            print(
                f"{x}".rjust(8),
                f"push({a}{x}{b})".ljust(12),
                stack,
                sep=" | ",
            )
    if len(stack) != 1:
        raise ArithmeticError("Input is not a valid postfix expression")
    return float(stack[0])
