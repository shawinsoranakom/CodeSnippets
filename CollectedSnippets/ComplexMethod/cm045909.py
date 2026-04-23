def to_4d(
            self,
            attention_mask_2d,
            query_length,
            dtype,
            key_value_length,
            use_parallel=False,
            parallel_step=3,
            is_export=False,
    ):
        """
        Converts 2D attention mask to 4D attention mask by expanding mask to (bsz, head_dim=1, query_length,
        key_value_length) shape and by adding a large negative bias to not-attended positions. If attention_mask is
        causal, a causal mask will be added.
        """
        input_shape = (attention_mask_2d.shape[0], query_length)

        causal_4d_mask = None
        if use_parallel:
            step = parallel_step
        else:
            step = 1
        if (
                input_shape[-1] > step or self.sliding_window is not None
        ) and self.is_causal:

            if key_value_length is None:
                raise ValueError(
                    "This attention mask converter is causal. Make sure to pass `key_value_length` to correctly create a causal mask."
                )

            past_key_values_length = key_value_length - query_length

            if use_parallel:
                causal_4d_mask = self._make_causal_mask_parallel(
                    input_shape,
                    dtype,
                    past_key_values_length=past_key_values_length,
                    sliding_window=self.sliding_window,
                    parallel_step=parallel_step,
                    is_export=is_export,
                )
            else:
                causal_4d_mask = self._make_causal_mask(
                    input_shape,
                    dtype,
                    past_key_values_length=past_key_values_length,
                    sliding_window=self.sliding_window,
                    is_export=is_export,
                )

        elif self.sliding_window is not None:
            raise NotImplementedError(
                "Sliding window is currently only implemented for causal masking"
            )

        expanded_attn_mask = self._expand_mask(
            attention_mask_2d, dtype, tgt_len=input_shape[-1]
        )

        if causal_4d_mask is not None:
            expanded_attn_mask = causal_4d_mask.masked_fill_(
                expanded_attn_mask.to(torch.bool), torch.finfo(dtype).min
            )

        expanded_4d_mask = expanded_attn_mask
        return expanded_4d_mask