def _stop_string_get_matching_positions(
        token_list, token_indices, stop_strings
    ) -> tuple[dict[str, dict[str, list[int]]], dict[str, dict[str, list[int]]]]:
        """This function preprocesses stop strings and the tokenizer vocabulary to determine where tokens can
        validly appear in the stop strings. For each token, it computes a list of positions in the stop string where the
        token appears, as well as a list of the possible "end overlaps" for that token - that is, the number of characters
        from the end of the stop string that overlap with the start of the token, which can have more than one value.

        The reason for computing these may seem a bit cryptic - please see the docstring for StopStringCriteria for a full
        explanation of what these values are for!"""

        token_valid_positions = {}
        token_end_overlaps = {}
        for stop_string in stop_strings:
            reversed_stop_string = stop_string[::-1]
            token_valid_positions[stop_string] = {}
            token_end_overlaps[stop_string] = {}
            for token, tok_idx in zip(token_list, token_indices):
                reversed_token = token[::-1]
                matching_positions = []
                possible_end_lengths = []
                for i in range(1 - len(token), len(stop_string)):
                    if i < 0:
                        tok = reversed_token[-i:]
                        i = 0
                    else:
                        tok = reversed_token
                    stop = reversed_stop_string[i : i + len(tok)]
                    if tok.startswith(stop):
                        if i == 0:
                            possible_end_lengths.append(min(len(tok), len(stop)))
                        else:
                            matching_positions.append(i)

                if matching_positions:
                    token_valid_positions[stop_string][tok_idx] = matching_positions
                if possible_end_lengths:
                    token_end_overlaps[stop_string][tok_idx] = possible_end_lengths
        return token_valid_positions, token_end_overlaps