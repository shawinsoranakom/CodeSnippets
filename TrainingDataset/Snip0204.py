def encrypt_message(key: int, message: str) -> str:
   
    key_a, key_b = divmod(key, len(SYMBOLS))
    check_keys(key_a, key_b, "encrypt")
    cipher_text = ""
    for symbol in message:
        if symbol in SYMBOLS:
            sym_index = SYMBOLS.find(symbol)
            cipher_text += SYMBOLS[(sym_index * key_a + key_b) % len(SYMBOLS)]
        else:
            cipher_text += symbol
    return cipher_text
