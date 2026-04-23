def _split_delta(
        self,
        delta_text: str,
        stop_after_quotes: int = -1,
        stop_after_opening_curly_braces: int = -1,
        stop_after_closing_curly_braces: int = -1,
        stop_after_closing_brackets: int = -1,
        stop_after_colon: int = -1,
        stop_after_comma=-1,
    ) -> tuple[str, str]:
        delta_to_be_parsed = ""
        for i, c in enumerate(delta_text):
            if c in ['"', "'"]:
                delta_to_be_parsed += c
                stop_after_quotes -= 1
                if stop_after_quotes == 0:
                    return (delta_to_be_parsed, delta_text[i + 1 :])
            elif c == "{":
                delta_to_be_parsed += c
                stop_after_opening_curly_braces -= 1
                if stop_after_opening_curly_braces == 0:
                    return (delta_to_be_parsed, delta_text[i + 1 :])
            elif c == "}":
                delta_to_be_parsed += c
                stop_after_closing_curly_braces -= 1
                if stop_after_closing_curly_braces == 0:
                    return (delta_to_be_parsed, delta_text[i + 1 :])
            elif c == "]":
                delta_to_be_parsed += c
                stop_after_closing_brackets -= 1
                if stop_after_closing_brackets == 0:
                    return (delta_to_be_parsed, delta_text[i + 1 :])
            elif c == ":":
                delta_to_be_parsed += c
                stop_after_colon -= 1
                if stop_after_colon == 0:
                    return (delta_to_be_parsed, delta_text[i + 1 :])
            elif c == ",":
                delta_to_be_parsed += c
                stop_after_comma -= 1
                if stop_after_comma == 0:
                    return (delta_to_be_parsed, delta_text[i + 1 :])
            else:
                delta_to_be_parsed += c

        return (delta_to_be_parsed, "")