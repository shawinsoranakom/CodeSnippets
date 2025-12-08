def __decrypt_part(
    message_part: str, character_to_number: dict[str, str]
) -> tuple[str, str, str]:
    this_part = "".join(character_to_number[character] for character in message_part)
    result = []
    tmp = ""
    for digit in this_part:
        tmp += digit
        if len(tmp) == len(message_part):
            result.append(tmp)
            tmp = ""

    return result[0], result[1], result[2]
