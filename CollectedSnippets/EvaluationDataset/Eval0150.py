def decompress_data(data_bits: str) -> str:

    lexicon = {"0": "0", "1": "1"}
    result, curr_string = "", ""
    index = len(lexicon)

    for i in range(len(data_bits)):
        curr_string += data_bits[i]
        if curr_string not in lexicon:
            continue

        last_match_id = lexicon[curr_string]
        result += last_match_id
        lexicon[curr_string] = last_match_id + "0"

        if math.log2(index).is_integer():
            new_lex = {}
            for curr_key in list(lexicon):
                new_lex["0" + curr_key] = lexicon.pop(curr_key)
            lexicon = new_lex

        lexicon[bin(index)[2:]] = last_match_id + "1"
        index += 1
        curr_string = ""
    return result
