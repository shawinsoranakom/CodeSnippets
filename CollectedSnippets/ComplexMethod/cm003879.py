def _convert_entity(match):
        entity_body = match.group(3)
        if match.group(1):
            try:
                if match.group(2):
                    number = int(entity_body, 16)
                else:
                    number = int(entity_body, 10)
                # Numeric character references in the 80-9F range are typically
                # interpreted by browsers as representing the characters mapped
                # to bytes 80-9F in the Windows-1252 encoding. For more info
                # see: https://en.wikipedia.org/wiki/ISO/IEC_8859-1#Similar_character_sets
                if 0x80 <= number <= 0x9F:
                    return bytes((number,)).decode("cp1252")
            except ValueError:
                number = None
        else:
            if entity_body in keep:
                return match.group(0)
            else:
                number = html.entities.name2codepoint.get(entity_body)
        if number is not None:
            try:
                return chr(number)
            except (ValueError, OverflowError):
                pass

        return "" if remove_illegal else match.group(0)