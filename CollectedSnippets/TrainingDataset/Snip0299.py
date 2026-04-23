def running_key_encrypt(key: str, plaintext: str) -> str:
    plaintext = plaintext.replace(" ", "").upper()
    key = key.replace(" ", "").upper()
    key_length = len(key)
    ciphertext = []
    ord_a = ord("A")

    for i, char in enumerate(plaintext):
        p = ord(char) - ord_a
        k = ord(key[i % key_length]) - ord_a
        c = (p + k) % 26
        ciphertext.append(chr(c + ord_a))

    return "".join(ciphertext)
