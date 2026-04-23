def _validate_message_attribute_name(name: str) -> None:
    """
    Validate the message attribute name with the specification of AWS.
    The message attribute name can contain the following characters: A-Z, a-z, 0-9, underscore(_), hyphen(-), and period (.). The name must not start or end with a period, and it should not have successive periods.
    :param name: message attribute name
    :raises InvalidParameterValueException: if the name does not conform to the spec
    """
    if not MSG_ATTR_NAME_REGEX.match(name):
        # find the proper exception
        if name[0] == ".":
            raise InvalidParameterValueException(
                "Invalid message attribute name starting with character '.' was found."
            )
        elif name[-1] == ".":
            raise InvalidParameterValueException(
                "Invalid message attribute name ending with character '.' was found."
            )

        for idx, char in enumerate(name):
            if char not in VALID_MSG_ATTR_NAME_CHARS:
                # change prefix from 0x to #x, without capitalizing the x
                hex_char = "#x" + hex(ord(char)).upper()[2:]
                raise InvalidParameterValueException(
                    f"Invalid non-alphanumeric character '{hex_char}' was found in the message attribute name. Can only include alphanumeric characters, hyphens, underscores, or dots."
                )
            # even if we go negative index, it will be covered by starting/ending with dot
            if char == "." and name[idx - 1] == ".":
                raise InvalidParameterValueException(
                    "Message attribute name can not have successive '.' character."
                )