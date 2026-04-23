def forward_impl(
        self,
        q: torch.Tensor,
        kv_c: torch.Tensor,
        k_pe: torch.Tensor,
        kv_cache: torch.Tensor,
        attn_metadata,
        output: torch.Tensor,
    ) -> torch.Tensor:
        """Replicates MLAAttention.forward_impl logic for testing."""
        # Write to KV cache
        kv_cache_dtype = getattr(self.impl, "kv_cache_dtype", "auto")
        fp8_attention = kv_cache_dtype.startswith("fp8")
        if kv_cache.numel() > 0:
            ops.concat_and_cache_mla(
                kv_c,
                k_pe.squeeze(1),
                kv_cache,
                attn_metadata.slot_mapping.flatten(),
                kv_cache_dtype=kv_cache_dtype,
                scale=self._k_scale,
            )

        if fp8_attention and kv_cache_dtype != "fp8_ds_mla":
            kv_cache = kv_cache.view(current_platform.fp8_dtype())

        # Determine decode vs prefill split
        num_decode_tokens = attn_metadata.num_decode_tokens or 0
        has_decode = (attn_metadata.num_decodes or 0) > 0
        has_prefill = (attn_metadata.num_prefills or 0) > 0

        # Run prefill with forward_mha
        if has_prefill:
            prefill_q = q[num_decode_tokens:]
            prefill_k_pe = k_pe[num_decode_tokens:]
            prefill_k_c = kv_c[num_decode_tokens:]
            self.impl.forward_mha(
                prefill_q,
                prefill_k_c,
                prefill_k_pe,
                kv_cache,
                attn_metadata,
                self._k_scale,
                output=output[num_decode_tokens:],
            )

        # Run decode with forward_mqa
        if has_decode:
            decode_q = q[:num_decode_tokens]

            # Split q into nope and pe parts
            mqa_q_nope, mqa_q_pe = decode_q.split(
                [self.qk_nope_head_dim, self.qk_rope_head_dim], dim=-1
            )

            # Convert from (B, N, P) to (N, B, P)
            mqa_q_nope = mqa_q_nope.transpose(0, 1)

            # Multiply (N, B, P) x (N, P, L) -> (N, B, L)
            mqa_ql_nope = torch.bmm(mqa_q_nope, self.W_UK_T)

            # Convert from (N, B, L) to (B, N, L)
            mqa_ql_nope = mqa_ql_nope.transpose(0, 1)

            if fp8_attention and self.impl.supports_quant_query_input:
                assert mqa_ql_nope.shape[0] == mqa_q_pe.shape[0]
                assert mqa_ql_nope.shape[1] == mqa_q_pe.shape[1]
                mqa_q = self._decode_concat_quant_fp8_op(
                    mqa_ql_nope, mqa_q_pe, self._q_scale
                )
            else:
                mqa_q = (mqa_ql_nope, mqa_q_pe)

            attn_out, _ = self.impl.forward_mqa(mqa_q, kv_cache, attn_metadata, self)

            # v_up projection: multiply by W_UV
            # attn_out shape: (B, N, L) where L = kv_lora_rank
            # W_UV shape: (N, L, V)
            # output shape: (B, N, V) -> flatten to (B, N*V)
            decode_output = torch.bmm(attn_out.transpose(0, 1), self.W_UV).transpose(
                0, 1
            )
            output[:num_decode_tokens] = decode_output.reshape(
                num_decode_tokens, self.num_heads * self.v_head_dim
            )

        return output