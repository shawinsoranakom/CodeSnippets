def decode(encoded: list[int]) -> str:
 
    return "".join(chr(elem + 96) for elem in encoded)
