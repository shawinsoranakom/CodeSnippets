def encrypt_fractionated_morse(plaintext: str, key: str) -> str:
   
    morse_code = encode_to_morse(plaintext)
    key = key.upper() + string.ascii_uppercase
    key = "".join(sorted(set(key), key=key.find))

    padding_length = 3 - (len(morse_code) % 3)
    morse_code += "x" * padding_length

    fractionated_morse_dict = {v: k for k, v in zip(key, MORSE_COMBINATIONS)}
    fractionated_morse_dict["xxx"] = ""
    encrypted_text = "".join(
        [
            fractionated_morse_dict[morse_code[i : i + 3]]
            for i in range(0, len(morse_code), 3)
        ]
    )
    return encrypted_text
