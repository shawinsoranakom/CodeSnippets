def __prepare(
    message: str, alphabet: str
) -> tuple[str, str, dict[str, str], dict[str, str]]:
   
    alphabet = alphabet.replace(" ", "").upper()
    message = message.replace(" ", "").upper()

    if len(alphabet) != 27:
        raise KeyError("Length of alphabet has to be 27.")
    if any(char not in alphabet for char in message):
        raise ValueError("Each message character has to be included in alphabet!")

    character_to_number = dict(zip(alphabet, TEST_CHARACTER_TO_NUMBER.values()))
    number_to_character = {
        number: letter for letter, number in character_to_number.items()
    }

    return message, alphabet, character_to_number, number_to_character
