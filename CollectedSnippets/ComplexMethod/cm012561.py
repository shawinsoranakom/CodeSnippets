def _all_in_parens(string: str) -> bool:
    if string[0] != "(" or len(string) < 2:
        return False
    count = 1
    for i, char in enumerate(string[1:]):
        if char == "(":
            count += 1
        elif char == ")":
            count -= 1
        if count == 0 and i != len(string) - 2:
            return False
    assert count == 0
    return True