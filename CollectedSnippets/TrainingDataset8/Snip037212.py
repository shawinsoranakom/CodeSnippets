def extract_args(line):
    """Parse argument strings from all outer parentheses in a line of code.

    Parameters
    ----------
    line : str
        A line of code

    Returns
    -------
    list of strings
        Contents of the outer parentheses

    Example
    -------
    >>> line = 'foo(bar, baz), "a", my(func)'
    >>> extract_args(line)
    ['bar, baz', 'func']

    """
    stack = 0
    startIndex = None
    results = []

    for i, c in enumerate(line):
        if c == "(":
            if stack == 0:
                startIndex = i + 1
            stack += 1
        elif c == ")":
            stack -= 1
            if stack == 0:
                results.append(line[startIndex:i])
    return results