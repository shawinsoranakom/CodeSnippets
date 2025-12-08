def __encrypt_part(message_part: str, character_to_number: dict[str, str]) -> str:
    one, two, three = "", "", ""
    for each in (character_to_number[character] for character in message_part):
        one += each[0]
        two += each[1]
        three += each[2]

    return one + two + three
