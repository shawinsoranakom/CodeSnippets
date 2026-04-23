def _get_score(text: str) -> tuple[str, int] | None:
    match = re.search(r"grade:\s*(correct|incorrect)", text.strip(), re.IGNORECASE)
    if match:
        if match.group(1).upper() == "CORRECT":
            return "CORRECT", 1
        if match.group(1).upper() == "INCORRECT":
            return "INCORRECT", 0
    try:
        first_word = (
            text.strip().split()[0].translate(str.maketrans("", "", string.punctuation))
        )
        if first_word.upper() == "CORRECT":
            return "CORRECT", 1
        if first_word.upper() == "INCORRECT":
            return "INCORRECT", 0
        last_word = (
            text.strip()
            .split()[-1]
            .translate(str.maketrans("", "", string.punctuation))
        )
        if last_word.upper() == "CORRECT":
            return "CORRECT", 1
        if last_word.upper() == "INCORRECT":
            return "INCORRECT", 0
    except IndexError:
        pass
    return None