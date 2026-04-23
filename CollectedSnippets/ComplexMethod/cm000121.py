def recursive_match(text: str, pattern: str) -> bool:
    r"""
    Recursive matching algorithm.

    | Time complexity: O(2^(\|text\| + \|pattern\|))
    | Space complexity: Recursion depth is O(\|text\| + \|pattern\|).

    :param text: Text to match.
    :param pattern: Pattern to match.
    :return: ``True`` if `text` matches `pattern`, ``False`` otherwise.

    >>> recursive_match('abc', 'a.c')
    True
    >>> recursive_match('abc', 'af*.c')
    True
    >>> recursive_match('abc', 'a.c*')
    True
    >>> recursive_match('abc', 'a.c*d')
    False
    >>> recursive_match('aa', '.*')
    True
    """
    if not pattern:
        return not text

    if not text:
        return pattern[-1] == "*" and recursive_match(text, pattern[:-2])

    if text[-1] == pattern[-1] or pattern[-1] == ".":
        return recursive_match(text[:-1], pattern[:-1])

    if pattern[-1] == "*":
        return recursive_match(text[:-1], pattern) or recursive_match(
            text, pattern[:-2]
        )

    return False