def _stop_string_create_embedding_vec(token_list, token_indices, stop_strings) -> dict[str, torch.Tensor]:
        """This function precomputes everything needed for the run-time checks in StopStringCriteria, and packs
        them into an embedding tensor that can be accessed with pure tensor operations. For the specifics of the values
        that are precomputed and what they are used for, please refer to the StopStringCriteria docstring!"""
        token_valid_positions, token_end_overlaps = StopStringCriteria._stop_string_get_matching_positions(
            token_list, token_indices, stop_strings
        )
        all_valid_positions = [len(val) for positions in token_valid_positions.values() for val in positions.values()]
        # In some cases, tokens may have no valid internal positions (such as single-character stop strings), so
        # we need a fallback to handle this case
        max_valid_positions = max(all_valid_positions) if all_valid_positions else 1
        # There should always be at least one valid end_len, however, so no fallback needed here
        valid_end_lens = [len(val) for positions in token_end_overlaps.values() for val in positions.values()]
        if not valid_end_lens:
            raise ValueError(
                "Stop string preprocessing was unable to identify tokens matching one or more of the "
                "supplied stop string(s). This is most often caused by the stop "
                "strings containing unusual characters that are not in the tokenizer vocabulary."
            )
        max_valid_end_lens = max(valid_end_lens)
        vec_size = len(stop_strings) * (max_valid_positions + max_valid_end_lens) + 1
        # We use +2 instead of +1 so we can have a dummy entry at the end. We will clamp all token values
        # over the max to this, ensuring they do not contribute to stop string matching.
        gather_vec = np.full((max(token_indices) + 2, vec_size), dtype=np.int32, fill_value=-1)

        for i, stop_string in enumerate(stop_strings):
            positions = token_valid_positions[stop_string]
            end_lens = token_end_overlaps[stop_string]

            # Since this is lots of very small assignments of lists, we build it with numpy rather
            # than torch for speed + simplicity, then convert to torch at the end
            for token_idx, valid_positions in positions.items():
                gather_vec[token_idx, max_valid_positions * i : max_valid_positions * i + len(valid_positions)] = (
                    valid_positions
                )
            for token_idx, possible_end_lens in end_lens.items():
                gather_vec[
                    token_idx,
                    max_valid_positions * len(stop_strings) + max_valid_end_lens * i : max_valid_positions
                    * len(stop_strings)
                    + max_valid_end_lens * i
                    + len(possible_end_lens),
                ] = possible_end_lens
            for token, token_idx in zip(token_list, token_indices):
                gather_vec[token_idx, -1] = len(token)

        gather_vec = torch.tensor(gather_vec, dtype=torch.int32)

        return gather_vec, max_valid_positions, max_valid_end_lens