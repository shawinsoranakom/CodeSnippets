def create_token_type_ids_from_sequences(
        self, token_ids_0: list[int], token_ids_1: list[int] | None = None
    ) -> list[int]:
        """
        Create a mask from the two sequences passed to be used in a sequence-pair classification task.

        This method dynamically builds the token type IDs based on the tokenizer's configuration attributes:
        - `token_type_ids_pattern`: Pattern to use ("all_zeros" or "bert_style")
        - `token_type_ids_include_special_tokens`: Whether to account for special tokens in length calculation

        Args:
            token_ids_0 (`list[int]`):
                List of IDs.
            token_ids_1 (`list[int]`, *optional*):
                Optional second list of IDs for sequence pairs.

        Returns:
            `list[int]`: Token type IDs according to the configured pattern.

        Examples:
            ```python
            # All zeros pattern (default, used by RoBERTa, BART, etc.)
            tokenizer.token_type_ids_pattern = "all_zeros"
            # Returns: [0, 0, 0, ...] for both sequences

            # BERT-style pattern (first sequence gets 0s, second gets 1s)
            tokenizer.token_type_ids_pattern = "bert_style"
            # Returns: [0, 0, 0, ..., 1, 1, 1, ...] for sequence pairs
            ```
        """
        # Calculate lengths - account for special tokens if configured
        if self.token_type_ids_include_special_tokens:
            # Build the full sequence to get accurate length
            if token_ids_1 is None:
                sequence = self.build_inputs_with_special_tokens(token_ids_0)
                seq0_len = len(sequence)
                seq1_len = 0
            else:
                full_sequence = self.build_inputs_with_special_tokens(token_ids_0, token_ids_1)
                # Approximate split - this works for most tokenizers
                # For more complex cases, subclasses should still override
                seq0_with_special = self.build_inputs_with_special_tokens(token_ids_0)
                seq0_len = len(seq0_with_special)
                seq1_len = len(full_sequence) - seq0_len
        else:
            # Use raw token lengths
            seq0_len = len(token_ids_0)
            seq1_len = len(token_ids_1) if token_ids_1 is not None else 0

        # Build token type IDs based on pattern
        if self.special_tokens_pattern == "prefix_suffix":
            total_len = len(getattr(self, "prefix_tokens", [])) + len(token_ids_0)
            if token_ids_1 is not None:
                total_len += len(token_ids_1)
            total_len += len(getattr(self, "suffix_tokens", []))
            return [0] * total_len

        if self.token_type_ids_pattern == "bert_style" and token_ids_1 is not None:
            # BERT-style: first sequence gets 0s, second sequence gets 1s
            return [0] * seq0_len + [1] * seq1_len
        else:
            # All zeros pattern (default): everything gets 0s
            return [0] * (seq0_len + seq1_len)