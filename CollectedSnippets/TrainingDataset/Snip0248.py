def encode_to_morse(plaintext: str) -> str:
  
    return "x".join([MORSE_CODE_DICT.get(letter.upper(), "") for letter in plaintext])
