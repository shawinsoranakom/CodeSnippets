def encrypt(message: str) -> str:
    return " ".join(MORSE_CODE_DICT[char] for char in message.upper())
