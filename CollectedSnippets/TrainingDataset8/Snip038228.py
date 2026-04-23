def snake_case_to_camel_case(snake_case_string: str) -> str:
    """Transform input string from snake_case to CamelCase."""
    words = snake_case_string.split("_")
    capitalized_words_arr = []

    for word in words:
        if word:
            try:
                capitalized_words_arr.append(word.title())
            except Exception:
                capitalized_words_arr.append(word)
    return "".join(capitalized_words_arr)