def decrypt(encrypted_message: str, key: list[int]) -> str:

    key_length = len(key)
    decrypted_message = ""

    for i in range(0, len(encrypted_message), key_length):
        block = encrypted_message[i : i + key_length]
        original_block = [""] * key_length
        for j, digit in enumerate(key):
            original_block[digit] = block[j]
        decrypted_message += "".join(original_block)

    return decrypted_message
