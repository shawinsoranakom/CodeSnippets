def decrypt(ciphertext: str, key: str) -> str:
   
    if not isinstance(ciphertext, str):
        raise TypeError("ciphertext must be a string")
    if not isinstance(key, str):
        raise TypeError("key must be a string")

    if not ciphertext:
        raise ValueError("ciphertext is empty")
    if not key:
        raise ValueError("key is empty")

    key = key.lower()
    ciphertext_iterator = 0
    key_iterator = 0
    plaintext = ""
    while ciphertext_iterator < len(ciphertext):
        if (
            ord(ciphertext[ciphertext_iterator]) < 97
            or ord(ciphertext[ciphertext_iterator]) > 122
        ):
            plaintext += ciphertext[ciphertext_iterator]
        else:
            plaintext += chr(
                (ord(ciphertext[ciphertext_iterator]) - ord(key[key_iterator])) % 26
                + 97
            )
            key += chr(
                (ord(ciphertext[ciphertext_iterator]) - ord(key[key_iterator])) % 26
                + 97
            )
            key_iterator += 1
        ciphertext_iterator += 1
    return plaintext
