def evaluate(post_fix: list[str], verbose: bool = False) -> float:
    """
    Evaluate postfix expression using a stack.
    >>> evaluate(["0"])
    0.0
    >>> evaluate(["-0"])
    -0.0
    >>> evaluate(["1"])
    1.0
    >>> evaluate(["-1"])
    -1.0
    >>> evaluate(["-1.1"])
    -1.1
    >>> evaluate(["2", "1", "+", "3", "*"])
    9.0
    >>> evaluate(["2", "1.9", "+", "3", "*"])
    11.7
    >>> evaluate(["2", "-1.9", "+", "3", "*"])
    0.30000000000000027
    >>> evaluate(["4", "13", "5", "/", "+"])
    6.6
    >>> evaluate(["2", "-", "3", "+"])
    1.0
    >>> evaluate(["-4", "5", "*", "6", "-"])
    -26.0
    >>> evaluate([])
    0
    >>> evaluate(["4", "-", "6", "7", "/", "9", "8"])
    Traceback (most recent call last):
    ...
    ArithmeticError: Input is not a valid postfix expression

    Parameters
    ----------
    post_fix:
        The postfix expression is tokenized into operators and operands and stored
        as a Python list

    verbose:
        Display stack contents while evaluating the expression if verbose is True

    Returns
    -------
    float
        The evaluated value
    """
    if not post_fix:
        return 0
    # Checking the list to find out whether the postfix expression is valid
    valid_expression = [parse_token(token) for token in post_fix]
    if verbose:
        # print table header
        print("Symbol".center(8), "Action".center(12), "Stack", sep=" | ")
        print("-" * (30 + len(post_fix)))
    stack = []
    for x in valid_expression:
        if x not in OPERATORS:
            stack.append(x)  # append x to stack
            if verbose:
                # output in tabular format
                print(
                    f"{x}".rjust(8),
                    f"push({x})".ljust(12),
                    stack,
                    sep=" | ",
                )
            continue
        # If x is operator
        # If only 1 value is inside the stack and + or - is encountered
        # then this is unary + or - case
        if x in UNARY_OP_SYMBOLS and len(stack) < 2:
            b = stack.pop()  # pop stack
            if x == "-":
                b *= -1  # negate b
            stack.append(b)
            if verbose:
                # output in tabular format
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
        b = stack.pop()  # pop stack
        if verbose:
            # output in tabular format
            print(
                "".rjust(8),
                f"pop({b})".ljust(12),
                stack,
                sep=" | ",
            )

        a = stack.pop()  # pop stack
        if verbose:
            # output in tabular format
            print(
                "".rjust(8),
                f"pop({a})".ljust(12),
                stack,
                sep=" | ",
            )
        # evaluate the 2 values popped from stack & push result to stack
        stack.append(OPERATORS[x](a, b))  # type: ignore[index]
        if verbose:
            # output in tabular format
            print(
                f"{x}".rjust(8),
                f"push({a}{x}{b})".ljust(12),
                stack,
                sep=" | ",
            )
    # If everything is executed correctly, the stack will contain
    # only one element which is the result
    if len(stack) != 1:
        raise ArithmeticError("Input is not a valid postfix expression")
    return float(stack[0])