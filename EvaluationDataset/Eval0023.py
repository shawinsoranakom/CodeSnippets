def create_cipher_map(key: str) -> dict[str, str]:
    alphabet = [chr(i + 65) for i in range(26)]
    key = remove_duplicates(key.upper())
    offset = len(key)
    cipher_alphabet = {alphabet[i]: char for i, char in enumerate(key)}

    for i in range(len(cipher_alphabet), 26):
        char = alphabet[i - offset]
        while char in key:
            offset -= 1
            char = alphabet[i - offset]
        cipher_alphabet[alphabet[i]] = char
    return cipher_alphabet
