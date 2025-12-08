def encipher(message: str, cipher_map: dict[str, str]) -> str:

    return "".join(cipher_map.get(ch, ch) for ch in message.upper())
