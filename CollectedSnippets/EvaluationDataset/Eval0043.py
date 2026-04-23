def vernam_decrypt(ciphertext: str, key: str) -> str:
    decrypted_text = ""
    for i in range(len(ciphertext)):
        ct = ord(ciphertext[i]) - ord(key[i % len(key)])
        while ct < 0:
            ct = 26 + ct
        decrypted_text += chr(65 + ct)
    return decrypted_text
