def add_key_to_lexicon(
    lexicon: dict[str, str], curr_string: str, index: int, last_match_id: str
) -> None:

    lexicon.pop(curr_string)
    lexicon[curr_string + "0"] = last_match_id

    if math.log2(index).is_integer():
        for curr_key, value in lexicon.items():
            lexicon[curr_key] = f"0{value}"

    lexicon[curr_string + "1"] = bin(index)[2:]
