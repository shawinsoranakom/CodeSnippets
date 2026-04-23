def numpy_mask_tokens(self, inputs: Any) -> tuple[Any, Any, Any, Any]:
        """
        The masked tokens to be predicted for a particular sequence are determined by the following algorithm:

            0. Start from the beginning of the sequence by setting `cur_len = 0` (number of tokens processed so far).
            1. Sample a `span_length` from the interval `[1, max_span_length]` (length of span of tokens to be masked)
            2. Reserve a context of length `context_length = span_length / plm_probability` to surround span to be
               masked
            3. Sample a starting point `start_index` from the interval `[cur_len, cur_len + context_length -
               span_length]` and mask tokens `start_index:start_index + span_length`
            4. Set `cur_len = cur_len + context_length`. If `cur_len < max_len` (i.e. there are tokens remaining in the
               sequence to be processed), repeat from Step 1.
        """
        if self.tokenizer.mask_token is None:
            raise ValueError(
                "This tokenizer does not have a mask token which is necessary for permutation language modeling."
                " Please add a mask token if you want to use this tokenizer."
            )

        if inputs.shape[1] % 2 != 0:
            raise ValueError(
                "This collator requires that sequence lengths be even to create a leakage-free perm_mask. Please see"
                " relevant comments in source code for details."
            )

        labels = np.copy(inputs)
        # Creating the mask and target_mapping tensors
        masked_indices = np.full(labels.shape, 0, dtype=bool)
        target_mapping = np.zeros((labels.shape[0], labels.shape[1], labels.shape[1]), dtype=np.float32)

        for i in range(labels.shape[0]):
            # Start from the beginning of the sequence by setting `cur_len = 0` (number of tokens processed so far).
            cur_len = 0
            max_len = labels.shape[1]

            while cur_len < max_len:
                # Sample a `span_length` from the interval `[1, max_span_length]` (length of span of tokens to be masked)
                span_length = randint(1, self.max_span_length + 1)
                # Reserve a context of length `context_length = span_length / plm_probability` to surround the span to be masked
                context_length = int(span_length / self.plm_probability)
                # Sample a starting point `start_index` from the interval `[cur_len, cur_len + context_length - span_length]` and mask tokens `start_index:start_index + span_length`
                start_index = cur_len + randint(0, context_length - span_length + 1)
                masked_indices[i, start_index : start_index + span_length] = 1
                # Set `cur_len = cur_len + context_length`
                cur_len += context_length

            # Since we're replacing non-masked tokens with -100 in the labels tensor instead of skipping them altogether,
            # the i-th predict corresponds to the i-th token.
            target_mapping[i] = np.eye(labels.shape[1])

        special_tokens_mask = np.array(
            [self.tokenizer.get_special_tokens_mask(val, already_has_special_tokens=True) for val in labels.tolist()],
            dtype=bool,
        )
        masked_indices[special_tokens_mask] = 0
        if self.tokenizer.pad_token is not None:
            padding_mask = labels == self.tokenizer.pad_token_id
            masked_indices[padding_mask] = 0.0

        # Mask indicating non-functional tokens, where functional tokens are [SEP], [CLS], padding, etc.
        non_func_mask = ~(padding_mask | special_tokens_mask)

        inputs[masked_indices] = self.tokenizer.mask_token_id
        labels[~masked_indices] = -100  # We only compute loss on masked tokens

        perm_mask = np.zeros((labels.shape[0], labels.shape[1], labels.shape[1]), dtype=np.float32)

        for i in range(labels.shape[0]):
            # Generate permutation indices i.e. sample a random factorisation order for the sequence. This will
            # determine which tokens a given token can attend to (encoded in `perm_mask`).
            # Note: Length of token sequence being permuted has to be less than or equal to reused sequence length
            # (see documentation for `mems`), otherwise information may leak through due to reuse. In this implementation,
            # we assume that reused length is half of sequence length and permutation length is equal to reused length.
            # This requires that the sequence length be even.

            # Create a linear factorisation order
            perm_index = np.arange(labels.shape[1])
            # Split this into two halves, assuming that half the sequence is reused each time
            perm_index = perm_index.reshape((-1, labels.shape[1] // 2)).T
            # Permute the two halves such that they do not cross over
            np.random.shuffle(perm_index)
            # Flatten this out into the desired permuted factorisation order
            perm_index = perm_index.T.flatten()
            # Set the permutation indices of non-masked (non-functional) tokens to the
            # smallest index (-1) so that:
            # (1) They can be seen by all other positions
            # (2) They cannot see masked positions, so there won't be information leak
            perm_index[~masked_indices[i] & non_func_mask[i]] = -1
            # The logic for whether the i-th token can attend on the j-th token based on the factorisation order:
            # 0 (can attend): If perm_index[i] > perm_index[j] or j is neither masked nor a functional token
            # 1 (cannot attend): If perm_index[i] <= perm_index[j] and j is either masked or a functional token
            perm_mask[i] = (
                perm_index.reshape((labels.shape[1], 1)) <= perm_index.reshape((1, labels.shape[1]))
            ) & masked_indices[i]

        return inputs.astype(np.int64), perm_mask, target_mapping, labels.astype(np.int64)