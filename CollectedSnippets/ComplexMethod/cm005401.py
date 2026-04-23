def numpy_mask_tokens(
        self,
        inputs: Any,
        special_tokens_mask: Any | None = None,
        offset_mapping: Any | None = None,
    ) -> tuple[Any, Any]:
        """
        Prepare masked tokens inputs/labels for masked language modeling.
        """
        labels = np.copy(inputs)
        # We sample a few tokens in each sequence for MLM training (with probability `self.mlm_probability`)
        probability_matrix = np.full(labels.shape, self.mlm_probability)
        if special_tokens_mask is None:
            special_tokens_mask = [
                self.tokenizer.get_special_tokens_mask(val, already_has_special_tokens=True) for val in labels.tolist()
            ]

        if self.whole_word_mask:
            word_ids, no_mask_mask = self._calc_word_ids_and_prob_mask(
                to_numpy(offset_mapping), to_numpy(special_tokens_mask)
            )
        else:
            no_mask_mask = (
                special_tokens_mask.astype(bool)
                if isinstance(special_tokens_mask, np.ndarray)
                else np.array(special_tokens_mask, dtype=bool)
            )

        probability_matrix[no_mask_mask] = 0
        # Numpy doesn't have bernoulli, so we use a binomial with 1 trial
        if self.generator:
            masked_indices = self.generator.binomial(1, probability_matrix, size=probability_matrix.shape).astype(bool)
        else:
            masked_indices = np.random.binomial(1, probability_matrix, size=probability_matrix.shape).astype(bool)

        if self.whole_word_mask:
            masked_indices = self._whole_word_mask(word_ids, masked_indices)

        labels[~masked_indices] = -100  # We only compute loss on masked tokens

        # mask_replace_prob% of the time, we replace masked input tokens with tokenizer.mask_token ([MASK])
        if self.generator:
            indices_replaced = (
                self.generator.binomial(1, self.mask_replace_prob, size=labels.shape).astype(bool) & masked_indices
            )
        else:
            indices_replaced = (
                np.random.binomial(1, self.mask_replace_prob, size=labels.shape).astype(bool) & masked_indices
            )
        inputs[indices_replaced] = self.tokenizer.mask_token_id

        if self.mask_replace_prob == 1 or self.random_replace_prob == 0:
            return inputs, labels

        remaining_prob = 1 - self.mask_replace_prob
        # scaling the random_replace_prob to the remaining probability for example if
        # mask_replace_prob = 0.8 and random_replace_prob = 0.1,
        # then random_replace_prob_scaled = 0.1 / 0.2 = 0.5
        random_replace_prob_scaled = self.random_replace_prob / remaining_prob
        if self.generator:
            indices_random = (
                self.generator.binomial(1, random_replace_prob_scaled, size=labels.shape).astype(bool)
                & masked_indices
                & ~indices_replaced
            )
            random_words = self.generator.integers(
                low=0, high=len(self.tokenizer), size=np.count_nonzero(indices_random), dtype=np.int64
            )
        else:
            indices_random = (
                np.random.binomial(1, random_replace_prob_scaled, size=labels.shape).astype(bool)
                & masked_indices
                & ~indices_replaced
            )
            random_words = np.random.randint(
                low=0, high=len(self.tokenizer), size=np.count_nonzero(indices_random), dtype=np.int64
            )
        inputs[indices_random] = random_words

        # The rest of the time (10% of the time) we keep the masked input tokens unchanged
        return inputs, labels