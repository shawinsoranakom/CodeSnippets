def forward_mha(
        self,
        q: torch.Tensor,
        kv_c_normed: torch.Tensor,
        k_pe: torch.Tensor,
        kv_c_and_k_pe_cache: torch.Tensor,
        attn_metadata: MLACommonMetadata,
        k_scale: torch.Tensor,
        output: torch.Tensor,
    ) -> None:
        # TODO (zyongye): Prefill function here
        assert attn_metadata.prefill is not None
        assert self.dcp_world_size != -1

        prefill_metadata = attn_metadata.prefill
        use_fp8_prefill = prefill_metadata.q_data_type == current_platform.fp8_dtype()

        # Convert q to FP8 if FP8 prefill attention is enabled
        if use_fp8_prefill:
            q = q.to(prefill_metadata.q_data_type)

        has_context = prefill_metadata.chunked_context is not None

        kv_nope = self.kv_b_proj(kv_c_normed)[0].view(
            -1, self.num_heads, self.qk_nope_head_dim + self.v_head_dim
        )
        k_nope, v = kv_nope.split([self.qk_nope_head_dim, self.v_head_dim], dim=-1)
        k = self._concat_k_nope_k_pe(k_nope, k_pe)

        if use_fp8_prefill:
            k = k.to(prefill_metadata.q_data_type)
            v = v.to(prefill_metadata.q_data_type)

        output_prefill = self._run_prefill_new_tokens(
            prefill=prefill_metadata,
            q=q,
            k=k,
            v=v,
            return_softmax_lse=has_context,
        )

        if has_context:
            assert prefill_metadata.chunked_context is not None
            suffix_output, suffix_lse = output_prefill
            if self.dcp_world_size > 1:
                context_output, context_lse = (
                    self._context_parallel_compute_prefill_context(
                        q,
                        kv_c_and_k_pe_cache,
                        attn_metadata,
                        k_scale=None,
                        dcp_world_size=self.dcp_world_size,
                    )
                )
            else:
                context_output, context_lse = self._compute_prefill_context(
                    q, kv_c_and_k_pe_cache, attn_metadata, k_scale
                )

            # unpad if necessary
            if self._pad_v:
                context_output = context_output[..., : v.shape[-1]]
                suffix_output = suffix_output[..., : v.shape[-1]]

            output = output.view(-1, self.num_heads, self.v_head_dim)
            merge_attn_states(
                output=output,
                prefix_output=context_output,
                prefix_lse=context_lse,
                suffix_output=suffix_output,
                suffix_lse=suffix_lse,
                prefill_tokens_with_context=prefill_metadata.chunked_context.prefill_tokens_with_context,
            )
        else:
            output_prefill = output_prefill[..., : v.shape[-1]].flatten(start_dim=-2)
            output.copy_(output_prefill)