def translate_message(key: str, message: str, mode: str) -> str:
    translated = ""
    chars_a = LETTERS
    chars_b = key

    if mode == "decrypt":
        chars_a, chars_b = chars_b, chars_a

    for symbol in message:
        if symbol.upper() in chars_a:
            sym_index = chars_a.find(symbol.upper())
            if symbol.isupper():
                translated += chars_b[sym_index].upper()
            else:
                translated += chars_b[sym_index].lower()
        else:
            translated += symbol

    return translated
