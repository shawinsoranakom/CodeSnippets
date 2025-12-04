def decrypt(input_string: str, key: int, alphabet: str | None = None) -> str:
    
    key *= -1

    return encrypt(input_string, key, alphabet)
