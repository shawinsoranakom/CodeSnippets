def generate_table(key: str) -> list[tuple[str, str]]:
    return [alphabet[char] for char in key.upper()]

