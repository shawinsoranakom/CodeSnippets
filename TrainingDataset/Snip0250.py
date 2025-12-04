def decrypt_fractionated_morse(ciphertext: str, key: str) -> str:
    
    key = key.upper() + string.ascii_uppercase
    key = "".join(sorted(set(key), key=key.find))

    inverse_fractionated_morse_dict = dict(zip(key, MORSE_COMBINATIONS))
    morse_code = "".join(
        [inverse_fractionated_morse_dict.get(letter, "") for letter in ciphertext]
    )
    decrypted_text = "".join(
        [REVERSE_DICT[code] for code in morse_code.split("x")]
    ).strip()
    return decrypted_text
