def _compute_prefill_context(
        self,
        q: torch.Tensor,
        kv_c_and_k_pe_cache: torch.Tensor,
        attn_metadata: MLACommonMetadata,
        k_scale: torch.Tensor,
    ):
        assert attn_metadata.prefill is not None
        prefill_metadata = attn_metadata.prefill
        assert prefill_metadata.chunked_context is not None

        use_fp8_prefill = prefill_metadata.q_data_type == current_platform.fp8_dtype()

        output = None
        iters = len(prefill_metadata.chunked_context.seq_tot)
        workspace = prefill_metadata.chunked_context.workspace

        if use_fp8_prefill:
            q = q.to(prefill_metadata.q_data_type)

        for i in range(iters):
            toks = prefill_metadata.chunked_context.seq_tot[i]
            if not use_fp8_prefill:
                ops.gather_and_maybe_dequant_cache(
                    src_cache=kv_c_and_k_pe_cache,
                    dst=workspace,
                    block_table=prefill_metadata.block_table,
                    cu_seq_lens=prefill_metadata.chunked_context.cu_seq_lens[i],
                    token_to_seq=prefill_metadata.chunked_context.token_to_seq[i],
                    num_tokens=prefill_metadata.chunked_context.chunk_total_token[i],
                    kv_cache_dtype=self.kv_cache_dtype,
                    scale=k_scale,
                    seq_starts=prefill_metadata.chunked_context.starts[i],
                )
            else:
                # FP8 path: gather cache without dequantization
                ops.cp_gather_cache(
                    src_cache=kv_c_and_k_pe_cache,
                    dst=workspace,
                    block_table=prefill_metadata.block_table,
                    cu_seq_lens=prefill_metadata.chunked_context.cu_seq_lens[i],
                    batch_size=attn_metadata.num_prefills,
                    seq_starts=prefill_metadata.chunked_context.starts[i],
                )

            # Extract kv_c_normed from workspace
            kv_c_normed = workspace[:toks][..., : self.kv_lora_rank]
            # When FP8 weights are used without FP8 prefill, kv_b_proj expects
            # model dtype input and will quantize internally.
            # For quantized layers (AWQ/GPTQ) that lack a .weight attribute,
            # use params_dtype which is the expected input dtype.
            _kv_b_proj_w_dtype = (
                self.kv_b_proj.weight.dtype
                if hasattr(self.kv_b_proj, "weight")
                else self.kv_b_proj.params_dtype
            )
            # For NVFP4, weights are packed uint8 — keep input in model dtype
            # since the NVFP4 linear layer quantizes internally.
            if (
                use_fp8_prefill or _kv_b_proj_w_dtype != current_platform.fp8_dtype()
            ) and _kv_b_proj_w_dtype != torch.uint8:
                kv_c_normed = kv_c_normed.to(self.kv_b_proj.weight.dtype)

            k_pe = workspace[:toks][..., self.kv_lora_rank :].unsqueeze(1)
            kv_nope = self.kv_b_proj(kv_c_normed)[0].view(
                -1, self.num_heads, self.qk_nope_head_dim + self.v_head_dim
            )

            # To Do: Use epilogue of kv_b_proj to generate fp8 kv_nope.
            if use_fp8_prefill:
                kv_nope = kv_nope.to(prefill_metadata.q_data_type)
                k_pe = k_pe.to(prefill_metadata.q_data_type)
            k_nope, v = kv_nope.split([self.qk_nope_head_dim, self.v_head_dim], dim=-1)

            k = self._concat_k_nope_k_pe(k_nope, k_pe)

            attn_output, attn_softmax_lse = self._run_prefill_context_chunk(
                prefill=prefill_metadata,
                chunk_idx=i,
                q=q,
                k=k,
                v=v,
            )

            if output is None:
                output = attn_output
                output_lse = attn_softmax_lse
            else:
                output_tmp = torch.empty_like(output)
                output_lse_tmp = torch.empty_like(output_lse)
                merge_attn_states(
                    output=output_tmp,
                    output_lse=output_lse_tmp,
                    prefix_output=output,
                    prefix_lse=output_lse,
                    suffix_output=attn_output,
                    suffix_lse=attn_softmax_lse,
                )
                output = output_tmp
                output_lse = output_lse_tmp

        return output, output_lse