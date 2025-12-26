def run_length_decode(encoded: list) -> str:

    return "".join(char * length for char, length in encoded)
