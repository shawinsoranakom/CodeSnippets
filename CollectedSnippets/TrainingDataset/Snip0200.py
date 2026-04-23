def encode(plain: str) -> list[int]:
 
    return [ord(elem) - 96 for elem in plain]
