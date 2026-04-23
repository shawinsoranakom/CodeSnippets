def torch_mask_tokens(
        self, inputs: Any, special_tokens_mask: Any | None = None, offset_mapping: Any | None = None
    ) -> tuple[Any, Any]:
        """
        Prepare masked tokens inputs/labels for masked language modeling.
        """
        import torch

        labels = inputs.clone()
        # We sample a few tokens in each sequence for MLM training (with probability `self.mlm_probability`)
        probability_matrix = torch.full(labels.shape, self.mlm_probability)
        if special_tokens_mask is None:
            special_tokens_mask = [
                self.tokenizer.get_special_tokens_mask(val, already_has_special_tokens=True) for val in labels.tolist()
            ]

        if self.whole_word_mask:
            word_ids, no_mask_mask = self._calc_word_ids_and_prob_mask(
                to_numpy(offset_mapping), to_numpy(special_tokens_mask)
            )
            no_mask_mask = torch.tensor(no_mask_mask, dtype=torch.bool)
        else:
            no_mask_mask = (
                special_tokens_mask.bool()
                if isinstance(special_tokens_mask, torch.Tensor)
                else torch.tensor(special_tokens_mask, dtype=torch.bool)
            )

        probability_matrix.masked_fill_(no_mask_mask, value=0.0)
        masked_indices = torch.bernoulli(probability_matrix, generator=self.generator).bool()
        if self.whole_word_mask:
            masked_indices = torch.BoolTensor(self._whole_word_mask(word_ids, masked_indices))

        labels[~masked_indices] = -100  # We only compute loss on masked tokens

        # mask_replace_prob% of the time, we replace masked input tokens with tokenizer.mask_token ([MASK])
        indices_replaced = (
            torch.bernoulli(torch.full(labels.shape, self.mask_replace_prob), generator=self.generator).bool()
            & masked_indices
        )
        inputs[indices_replaced] = self.tokenizer.convert_tokens_to_ids(self.tokenizer.mask_token)

        if self.mask_replace_prob == 1 or self.random_replace_prob == 0:
            return inputs, labels

        remaining_prob = 1 - self.mask_replace_prob
        # scaling the random_replace_prob to the remaining probability for example if
        # mask_replace_prob = 0.8 and random_replace_prob = 0.1,
        # then random_replace_prob_scaled = 0.1 / 0.2 = 0.5
        random_replace_prob_scaled = self.random_replace_prob / remaining_prob

        # random_replace_prob% of the time, we replace masked input tokens with random word
        indices_random = (
            torch.bernoulli(torch.full(labels.shape, random_replace_prob_scaled), generator=self.generator).bool()
            & masked_indices
            & ~indices_replaced
        )
        random_words = torch.randint(len(self.tokenizer), labels.shape, dtype=torch.long, generator=self.generator)
        inputs[indices_random] = random_words[indices_random]

        # The rest of the time ((1-random_replace_prob-mask_replace_prob)% of the time) we keep the masked input tokens unchanged
        return inputs, labels