def escape_brackets(self, token):
        characters = []
        consume_until_next_bracket = False
        for character in token:
            if character == "}":
                if consume_until_next_bracket:
                    consume_until_next_bracket = False
                else:
                    characters.append(character)
            if character == "{":
                n_backslashes = sum(
                    1 for char in _itertools.takewhile(
                        "\\".__eq__,
                        characters[-2::-1]
                    )
                )
                if n_backslashes % 2 == 0 or characters[-1] != "N":
                    characters.append(character)
                else:
                    consume_until_next_bracket = True
            characters.append(character)
        return "".join(characters)