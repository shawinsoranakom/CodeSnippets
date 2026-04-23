def _prepare_bias_variables(self, scores: torch.FloatTensor):
        vocabulary_size = scores.shape[-1]

        # Check biased tokens out of bounds
        invalid_biases = []
        for sequence_ids in self.sequence_bias:
            for token_id in sequence_ids:
                if token_id >= vocabulary_size:
                    invalid_biases.append(token_id)
        if len(invalid_biases) > 0:
            raise ValueError(
                f"The model vocabulary size is {vocabulary_size}, but the following tokens were being biased: "
                f"{invalid_biases}"
            )

        # Precompute the bias tensors to be applied. Sequences of length 1 are kept separately, as they can be applied
        # with simpler logic.
        self.length_1_bias = torch.zeros((vocabulary_size,), dtype=torch.float, device=scores.device)
        # Extract single-token sequences and their biases
        single_token_ids = []
        single_token_biases = []
        for sequence_ids, bias in self.sequence_bias.items():
            if len(sequence_ids) == 1:
                single_token_ids.append(sequence_ids[0])
                single_token_biases.append(bias)

        if single_token_ids:  # Only if we have any single-token sequences
            self.length_1_bias[single_token_ids] = torch.tensor(single_token_biases, device=scores.device)
        self.prepared_bias_variables = True