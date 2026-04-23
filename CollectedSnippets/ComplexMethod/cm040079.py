def _compute_attention(
        self, query, key, value, attention_mask=None, training=None
    ):
        # Check for flash attention constraints
        if self._flash_attention and self._return_attention_scores:
            raise ValueError(
                "Returning attention scores is not supported when flash "
                "attention is enabled. Please disable flash attention to access"
                " attention scores."
            )

        # Determine whether to use dot-product attention
        use_dot_product_attention = not (
            self.dropout > 0.0
            or self._return_attention_scores
            or (len(query.shape) != 4)
        )

        if use_dot_product_attention:
            if attention_mask is not None:
                # Ensure attention_mask has the correct shape for broadcasting
                # Expected shape: [batch_size, num_heads, query_seq_len,
                # key_seq_len].
                mask_expansion_axis = -1 * 2 - 1
                len_attention_scores_shape = 4  # Only accepts 4D inputs
                for _ in range(
                    len_attention_scores_shape - len(attention_mask.shape)
                ):
                    attention_mask = ops.expand_dims(
                        attention_mask, axis=mask_expansion_axis
                    )
                attention_mask = ops.cast(attention_mask, dtype="bool")
            # Directly compute the attention output using dot-product attention
            attention_output = ops.dot_product_attention(
                query=query,
                key=key,
                value=value,
                bias=None,
                mask=attention_mask,
                scale=self._inverse_sqrt_head_dim,
                is_causal=False,
                flash_attention=self._flash_attention,
            )
            return attention_output, None

        # Default behavior without flash attention, with explicit attention
        # scores
        query = ops.multiply(
            query, ops.cast(self._inverse_sqrt_head_dim, query.dtype)
        )
        # Take the dot product between "query" and "key" to get the raw
        # attention scores.
        scores = ops.einsum(
            self._dot_product_equation, query, key
        )  # (batch_dim, query_heads, target_seq_len, source_seq_len)
        scores = self._masked_softmax(scores, attention_mask=attention_mask)
        # This is actually dropping out entire tokens to attend to, which might
        # seem a bit unusual, but is taken from the original Transformer paper.
        if self.dropout > 0.0:
            scores_dropout = self._dropout_layer(scores, training=training)
        else:
            scores_dropout = scores
        output = ops.einsum(self._combine_equation, scores_dropout, value)
        return output, scores