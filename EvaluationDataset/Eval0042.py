def vernam_encrypt(plaintext: str, key: str) -> str:

    ciphertext = ""
    for i in range(len(plaintext)):
        ct = ord(key[i % len(key)]) - 65 + ord(plaintext[i]) - 65
        while ct > 25:
            ct = ct - 26
        ciphertext += chr(65 + ct)
    return ciphertext
