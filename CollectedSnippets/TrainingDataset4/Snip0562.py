def precedence(char: str) -> int:
    return PRECEDENCES.get(char, -1)
