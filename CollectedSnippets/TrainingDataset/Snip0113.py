def backtrack(input_string: str, word_dict: set[str], start: int) -> bool:

    if start == len(input_string):
        return True

    for end in range(start + 1, len(input_string) + 1):
        if input_string[start:end] in word_dict and backtrack(
            input_string, word_dict, end
        ):
            return True

    return False
