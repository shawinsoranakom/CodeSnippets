def word_break(input_string: str, word_dict: set[str]) -> bool:

    return backtrack(input_string, word_dict, 0)
