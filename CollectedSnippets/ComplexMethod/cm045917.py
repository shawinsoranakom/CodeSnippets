def to_4d(
            self,
            attention_mask_2d,
            query_length,
            dtype,
            key_value_length,
            is_export=False,
    ):

        input_shape = (attention_mask_2d.shape[0], query_length)
        causal_4d_mask = None
        if (input_shape[-1] > 1 or self.sliding_window is not None) and self.is_causal:
            if key_value_length is None:
                raise ValueError(
                    "This attention mask converter is causal. Make sure to pass `key_value_length` to correctly create a causal mask."
                )

            past_key_values_length = key_value_length - query_length

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
            if is_export:
                expanded_attn_mask = causal_4d_mask
                return expanded_attn_mask
            else:
                expanded_attn_mask = causal_4d_mask.masked_fill_(
                    expanded_attn_mask.to(torch.bool), torch.finfo(dtype).min
                )

        expanded_4d_mask = expanded_attn_mask

        return expanded_4d_mask