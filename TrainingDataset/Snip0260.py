def decrypt(message: str) -> str:
    return "".join(REVERSE_DICT[char] for char in message.split())
