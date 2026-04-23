def encrypt(plaintext: str, key: str) -> str:
    """
    Encrypt a given `plaintext` (string) and `key` (string), returning the
    encrypted ciphertext.

    >>> encrypt("hello world", "coffee")
    'jsqqs avvwo'
    >>> encrypt("coffee is good as python", "TheAlgorithms")
    'vvjfpk wj ohvp su ddylsv'
    >>> encrypt("coffee is good as python", 2)
    Traceback (most recent call last):
        ...
    TypeError: key must be a string
    >>> encrypt("", "TheAlgorithms")
    Traceback (most recent call last):
        ...
    ValueError: plaintext is empty
    >>> encrypt("coffee is good as python", "")
    Traceback (most recent call last):
        ...
    ValueError: key is empty
    >>> encrypt(527.26, "TheAlgorithms")
    Traceback (most recent call last):
        ...
    TypeError: plaintext must be a string
    """
    if not isinstance(plaintext, str):
        raise TypeError("plaintext must be a string")
    if not isinstance(key, str):
        raise TypeError("key must be a string")

    if not plaintext:
        raise ValueError("plaintext is empty")
    if not key:
        raise ValueError("key is empty")

    key += plaintext
    plaintext = plaintext.lower()
    key = key.lower()
    plaintext_iterator = 0
    key_iterator = 0
    ciphertext = ""
    while plaintext_iterator < len(plaintext):
        if (
            ord(plaintext[plaintext_iterator]) < 97
            or ord(plaintext[plaintext_iterator]) > 122
        ):
            ciphertext += plaintext[plaintext_iterator]
            plaintext_iterator += 1
        elif ord(key[key_iterator]) < 97 or ord(key[key_iterator]) > 122:
            key_iterator += 1
        else:
            ciphertext += chr(
                (
                    (ord(plaintext[plaintext_iterator]) - 97 + ord(key[key_iterator]))
                    - 97
                )
                % 26
                + 97
            )
            key_iterator += 1
            plaintext_iterator += 1
    return ciphertext