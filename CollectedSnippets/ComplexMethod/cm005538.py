def _validate_arguments(self):
        sequence_bias = self.sequence_bias
        if not isinstance(sequence_bias, dict) and not isinstance(sequence_bias, list) or len(sequence_bias) == 0:
            raise ValueError(
                f"`sequence_bias` has to be a non-empty dictionary, or non-empty list of lists but is {sequence_bias}."
            )
        if isinstance(sequence_bias, dict) and any(
            not isinstance(sequence_ids, tuple) for sequence_ids in sequence_bias
        ):
            raise ValueError(f"`sequence_bias` has to be a dict with tuples as keys, but is {sequence_bias}.")
        if isinstance(sequence_bias, dict) and any(
            any((not isinstance(token_id, (int, np.integer)) or token_id < 0) for token_id in sequence_ids)
            or len(sequence_ids) == 0
            for sequence_ids in sequence_bias
        ):
            raise ValueError(
                f"Each key in `sequence_bias` has to be a non-empty tuple of positive integers, but is "
                f"{sequence_bias}."
            )

        def all_token_bias_pairs_are_valid(sequence):
            return (
                isinstance(sequence[0], list)
                and all(isinstance(token_id, (int, np.integer)) and token_id > 0 for token_id in sequence[0])
                and isinstance(sequence[1], float)
            )

        if isinstance(sequence_bias, list) and any(
            (not all_token_bias_pairs_are_valid(sequence)) or len(sequence) == 0 for sequence in sequence_bias
        ):
            raise ValueError(
                f"Each element in `sequence_bias` has to be a non-empty list of lists of positive integers and float, but is "
                f"{sequence_bias}."
            )
        if isinstance(sequence_bias, dict) and any(not isinstance(bias, float) for bias in sequence_bias.values()):
            raise ValueError(f"`sequence_bias` has to be a dict with floats as values, but is {sequence_bias}.")