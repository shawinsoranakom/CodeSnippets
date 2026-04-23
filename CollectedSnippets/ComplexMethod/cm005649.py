def _find_longest_common_sequence(sequences, tokenizer):
    # TODO  Use a faster algorithm this can probably be done in O(n)
    # using suffix array.
    # It might be tedious to do because of fault tolerance.
    # We actually have a really good property which is that the total sequence
    # MUST be those subsequences in order.
    # Also the algorithm should be more tolerant to errors.
    sequence = [tok_id for tok_id in sequences[0][0].tolist() if tok_id not in tokenizer.all_special_ids]
    for new_seq in sequences[1:]:
        new_sequence = [tok_id for tok_id in new_seq[0].tolist() if tok_id not in tokenizer.all_special_ids]

        index = 0
        max_ = 0.0
        for i in range(1, len(new_sequence) + 1):
            # epsilon to favor long perfect matches
            eps = i / 10000.0
            matches = np.sum(np.array(sequence[-i:]) == np.array(new_sequence[:i]))
            matching = matches / i + eps
            if matches > 1 and matching > max_:
                index = i
                max_ = matching
        sequence.extend(new_sequence[index:])
    return np.array(sequence)