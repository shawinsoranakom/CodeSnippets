def decrypt_message(
    message: str, alphabet: str = "ABCDEFGHIJKLMNOPQRSTUVWXYZ.", period: int = 5
) -> str:

    message, alphabet, character_to_number, number_to_character = __prepare(
        message, alphabet
    )

    decrypted_numeric = []
    for i in range(0, len(message), period):
        a, b, c = __decrypt_part(message[i : i + period], character_to_number)

        for j in range(len(a)):
            decrypted_numeric.append(a[j] + b[j] + c[j])

    return "".join(number_to_character[each] for each in decrypted_numeric)
