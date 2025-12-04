def decrypt_message(key: int, message: str) -> str:
   
    key_a, key_b = divmod(key, len(SYMBOLS))
    check_keys(key_a, key_b, "decrypt")
    plain_text = ""
    mod_inverse_of_key_a = cryptomath.find_mod_inverse(key_a, len(SYMBOLS))
    for symbol in message:
        if symbol in SYMBOLS:
            sym_index = SYMBOLS.find(symbol)
            plain_text += SYMBOLS[
                (sym_index - key_b) * mod_inverse_of_key_a % len(SYMBOLS)
            ]
        else:
            plain_text += symbol
    return plain_text
