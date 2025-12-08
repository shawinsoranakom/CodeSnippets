def running_key_decrypt(key: str, ciphertext: str) -> str:
    """
    Decrypts the ciphertext using the Running Key Cipher.

    :param key: The running key (long piece of text).
    :param ciphertext: The ciphertext to be decrypted.
    :return: The plaintext.
    """
    ciphertext = ciphertext.replace(" ", "").upper()
    key = key.replace(" ", "").upper()
    key_length = len(key)
    plaintext = []
    ord_a = ord("A")

    for i, char in enumerate(ciphertext):
        c = ord(char) - ord_a
        k = ord(key[i % key_length]) - ord_a
        p = (c - k) % 26
        plaintext.append(chr(p + ord_a))

    return "".join(plaintext)
