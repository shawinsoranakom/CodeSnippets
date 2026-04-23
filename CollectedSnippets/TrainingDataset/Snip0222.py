def _base85_to_10(digits: list) -> int:
    return sum(char * 85**i for i, char in enumerate(reversed(digits)))
