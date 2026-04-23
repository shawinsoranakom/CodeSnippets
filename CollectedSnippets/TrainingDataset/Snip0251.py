def gronsfeld(text: str, key: str) -> str:
    
    ascii_len = len(ascii_uppercase)
    key_len = len(key)
    encrypted_text = ""
    keys = [int(char) for char in key]
    upper_case_text = text.upper()

    for i, char in enumerate(upper_case_text):
        if char in ascii_uppercase:
            new_position = (ascii_uppercase.index(char) + keys[i % key_len]) % ascii_len
            shifted_letter = ascii_uppercase[new_position]
            encrypted_text += shifted_letter
        else:
            encrypted_text += char

    return encrypted_text
