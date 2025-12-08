def decipher(message: str, cipher_map: dict[str, str]) -> str:

    rev_cipher_map = {v: k for k, v in cipher_map.items()}
    return "".join(rev_cipher_map.get(ch, ch) for ch in message.upper())
