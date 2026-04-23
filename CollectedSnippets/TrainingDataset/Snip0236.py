def decrypt_caesar_with_chi_squared(
    ciphertext: str,
    cipher_alphabet: list[str] | None = None,
    frequencies_dict: dict[str, float] | None = None,
    case_sensitive: bool = False,
) -> tuple[int, float, str]:
   
    alphabet_letters = cipher_alphabet or [chr(i) for i in range(97, 123)]

    if not frequencies_dict:
        frequencies = {
            "a": 0.08497,
            "b": 0.01492,
            "c": 0.02202,
            "d": 0.04253,
            "e": 0.11162,
            "f": 0.02228,
            "g": 0.02015,
            "h": 0.06094,
            "i": 0.07546,
            "j": 0.00153,
            "k": 0.01292,
            "l": 0.04025,
            "m": 0.02406,
            "n": 0.06749,
            "o": 0.07507,
            "p": 0.01929,
            "q": 0.00095,
            "r": 0.07587,
            "s": 0.06327,
            "t": 0.09356,
            "u": 0.02758,
            "v": 0.00978,
            "w": 0.02560,
            "x": 0.00150,
            "y": 0.01994,
            "z": 0.00077,
        }
    else:
        frequencies = frequencies_dict

    if not case_sensitive:
        ciphertext = ciphertext.lower()

    chi_squared_statistic_values: dict[int, tuple[float, str]] = {}

    for shift in range(len(alphabet_letters)):
        decrypted_with_shift = ""

        for letter in ciphertext:
            try:
                new_key = (alphabet_letters.index(letter.lower()) - shift) % len(
                    alphabet_letters
                )
                decrypted_with_shift += (
                    alphabet_letters[new_key].upper()
                    if case_sensitive and letter.isupper()
                    else alphabet_letters[new_key]
                )
            except ValueError:
                decrypted_with_shift += letter

        chi_squared_statistic = 0.0

        for letter in decrypted_with_shift:
            if case_sensitive:
                letter = letter.lower()
                if letter in frequencies:
                    occurrences = decrypted_with_shift.lower().count(letter)

                    expected = frequencies[letter] * occurrences

                    chi_letter_value = ((occurrences - expected) ** 2) / expected

                    chi_squared_statistic += chi_letter_value
            elif letter.lower() in frequencies:
                occurrences = decrypted_with_shift.count(letter)

                expected = frequencies[letter] * occurrences

                chi_letter_value = ((occurrences - expected) ** 2) / expected

                chi_squared_statistic += chi_letter_value

        chi_squared_statistic_values[shift] = (
            chi_squared_statistic,
            decrypted_with_shift,
        )

    def chi_squared_statistic_values_sorting_key(key: int) -> tuple[float, str]:
        return chi_squared_statistic_values[key]

    most_likely_cipher: int = min(
        chi_squared_statistic_values,
        key=chi_squared_statistic_values_sorting_key,
    )

    (
        most_likely_cipher_chi_squared_value,
        decoded_most_likely_cipher,
    ) = chi_squared_statistic_values[most_likely_cipher]

    return (
        most_likely_cipher,
        most_likely_cipher_chi_squared_value,
        decoded_most_likely_cipher,
    )
