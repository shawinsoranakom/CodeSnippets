def forward(
        self,
        input,
        mask,
        kv=None,
        cache=None,
        output_attentions=False,
        **kwargs,
    ):
        """
        Self-attention (if kv is None) or attention over source sentence (provided by kv).
        """
        # Input is (bs, qlen, dim)
        # Mask is (bs, klen) (non-causal) or (bs, klen, klen)
        bs, qlen, dim = input.size()
        is_cross_attention = kv is not None
        mask_reshape = (bs, 1, qlen, -1) if mask.dim() == 3 else (bs, 1, 1, -1)

        q = self.q_lin(input).view(bs, -1, self.n_heads, self.head_dim).transpose(1, 2)
        if cache is not None:
            if isinstance(cache, EncoderDecoderCache):
                is_updated = cache.is_updated.get(self.layer_id)
                if is_cross_attention:
                    # after the first generated id, we can subsequently re-use all key/value_states from cache
                    curr_past_key_values = cache.cross_attention_cache
                else:
                    curr_past_key_values = cache.self_attention_cache
            else:
                curr_past_key_values = cache

        current_states = kv if is_cross_attention else input
        if is_cross_attention and cache is not None and is_updated:
            # reuse k,v, cross_attentions
            k = curr_past_key_values.key_cache[self.layer_id]
            v = curr_past_key_values.value_cache[self.layer_id]
        else:
            k = self.k_lin(current_states)
            v = self.v_lin(current_states)
            k = k.view(bs, -1, self.n_heads, self.head_dim).transpose(1, 2)
            v = v.view(bs, -1, self.n_heads, self.head_dim).transpose(1, 2)

            if cache is not None:
                # save all key/value_states to cache to be re-used for fast auto-regressive generation
                k, v = curr_past_key_values.update(k, v, self.layer_id)
                # set flag that curr layer for cross-attn is already updated so we can re-use in subsequent calls
                if is_cross_attention:
                    cache.is_updated[self.layer_id] = True

        q = q / math.sqrt(self.head_dim)  # (bs, n_heads, qlen, head_dim)
        scores = torch.matmul(q, k.transpose(2, 3))  # (bs, n_heads, qlen, klen)
        mask = (mask == 0).view(mask_reshape).expand_as(scores)  # (bs, n_heads, qlen, klen)
        scores.masked_fill_(mask, torch.finfo(scores.dtype).min)  # (bs, n_heads, qlen, klen)

        weights = nn.functional.softmax(scores.float(), dim=-1).type_as(scores)  # (bs, n_heads, qlen, klen)
        weights = nn.functional.dropout(weights, p=self.dropout, training=self.training)  # (bs, n_heads, qlen, klen)

        context = torch.matmul(weights, v)  # (bs, n_heads, qlen, head_dim)
        context = context.transpose(1, 2).contiguous().view(bs, -1, self.n_heads * self.head_dim)

        outputs = (self.out_lin(context),)
        if output_attentions:
            outputs = outputs + (weights,)
        return outputs