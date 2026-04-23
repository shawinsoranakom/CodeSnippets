def is_reasoning_end(self, input_ids: Sequence[int]) -> bool:
        end_token_ids_prefix = self.reasoning_end_token_ids_prefix
        end_token_ids_suffix = self.reasoning_end_token_ids_suffix
        assert len(end_token_ids_prefix) > 0, "reasoning_end_token_ids_prefix is empty"
        assert len(end_token_ids_suffix) > 0, "reasoning_end_token_ids_suffix is empty"
        # Check if the end sequence is present in the input_ids.
        # We search from the end of input_ids to find the last match.
        for i in range(len(input_ids) - len(end_token_ids_prefix), -1, -1):
            if input_ids[i] == self.eom_token_id:
                # We looped backwards far enough to find the end of a previous message,
                # which means we have searched the entirety of the current message
                # and can exit early without searching further back into prior
                # messages of the conversation.
                return False
            if input_ids[i : i + len(end_token_ids_prefix)] == end_token_ids_prefix:
                # We have found the prefix, now we look for the suffix after the prefix.
                suffix_start = i + len(end_token_ids_prefix)
                for j in range(
                    suffix_start, len(input_ids) - len(end_token_ids_suffix) + 1
                ):
                    if j - suffix_start >= self.reasoning_max_num_between_tokens:
                        break
                    if (
                        input_ids[j : j + len(end_token_ids_suffix)]
                        == end_token_ids_suffix
                    ):
                        return True
        return False