def advanced_split(text: str) -> list[str]:
    result = []
    word = array('u')

    i = 0
    text_len = len(text)

    while i < text_len:
        char = text[i]
        o = ord(char)

        # Fast path for ASCII
        if o < 256 and SPLITS[o]:
            if word:
                result.append(word.tounicode())
                word = array('u')
        # Check for multi-char symbols
        elif i < text_len - 1:
            two_chars = char + text[i + 1]
            if two_chars in HTML_CODE_CHARS:
                if word:
                    result.append(word.tounicode())
                    word = array('u')
                i += 1  # Skip next char since we used it
            else:
                word.append(char)
        else:
            word.append(char)
        i += 1

    if word:
        result.append(word.tounicode())

    return result