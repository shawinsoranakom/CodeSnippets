def forward(
        self,
        x,
        context = None,
        mask = None,
        context_mask = None,
        rotary_pos_emb = None,
        causal = None,
        transformer_options={},
    ):
        h, kv_h, has_context = self.num_heads, self.kv_heads, context is not None

        kv_input = context if has_context else x

        if hasattr(self, 'to_q'):
            # Use separate linear projections for q and k/v
            q = self.to_q(x)
            q = rearrange(q, 'b n (h d) -> b h n d', h = h)

            k, v = self.to_kv(kv_input).chunk(2, dim=-1)

            k, v = map(lambda t: rearrange(t, 'b n (h d) -> b h n d', h = kv_h), (k, v))
        else:
            # Use fused linear projection
            q, k, v = self.to_qkv(x).chunk(3, dim=-1)
            q, k, v = map(lambda t: rearrange(t, 'b n (h d) -> b h n d', h = h), (q, k, v))

        # Normalize q and k for cosine sim attention
        if self.qk_norm:
            q = F.normalize(q, dim=-1)
            k = F.normalize(k, dim=-1)

        if rotary_pos_emb is not None and not has_context:
            freqs, _ = rotary_pos_emb

            q_dtype = q.dtype
            k_dtype = k.dtype

            q = q.to(torch.float32)
            k = k.to(torch.float32)
            freqs = freqs.to(torch.float32)

            q = apply_rotary_pos_emb(q, freqs)
            k = apply_rotary_pos_emb(k, freqs)

            q = q.to(q_dtype)
            k = k.to(k_dtype)

        input_mask = context_mask

        if input_mask is None and not has_context:
            input_mask = mask

        # determine masking
        masks = []

        if input_mask is not None:
            input_mask = rearrange(input_mask, 'b j -> b 1 1 j')
            masks.append(~input_mask)

        # Other masks will be added here later
        n = q.shape[-2]

        causal = self.causal if causal is None else causal

        if n == 1 and causal:
            causal = False

        if h != kv_h:
            # Repeat interleave kv_heads to match q_heads
            heads_per_kv_head = h // kv_h
            k, v = map(lambda t: t.repeat_interleave(heads_per_kv_head, dim = 1), (k, v))

        out = optimized_attention(q, k, v, h, skip_reshape=True, transformer_options=transformer_options)
        out = self.to_out(out)

        if mask is not None:
            mask = rearrange(mask, 'b n -> b n 1')
            out = out.masked_fill(~mask, 0.)

        return out