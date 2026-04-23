def encrypt(input_string: str, key: int, alphabet: str | None = None) -> str:
   
    alpha = alphabet or ascii_letters

    result = ""

    for character in input_string:
        if character not in alpha:
            result += character
        else:
            new_key = (alpha.index(character) + key) % len(alpha)

            result += alpha[new_key]

    return result
