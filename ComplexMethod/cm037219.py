def _forward_fp8_kv_separate_prefill_decode(
        self,
        q: torch.Tensor,
        kv_c_and_k_pe_cache: torch.Tensor,
        topk_indices: torch.Tensor,
        attn_metadata: FlashMLASparseMetadata,
    ) -> torch.Tensor:
        fp8_metadata = attn_metadata.fp8_extra_metadata
        assert isinstance(fp8_metadata, FlashMLASparseMetadata.FP8SeparatePrefillDecode)
        num_decodes = fp8_metadata.num_decodes

        prefill_request_ids = None
        prefill_workspace_starts = None
        has_prefill_workspace = False
        if fp8_metadata.prefill is not None:
            prefill_request_ids = fp8_metadata.prefill.request_ids
            prefill_workspace_starts = fp8_metadata.prefill.workspace_starts
            has_prefill_workspace = True

        # Convert per-request indices to global slots (decode) or workspace
        # offsets (prefill).
        # For FP8 cache: prefill uses workspace mapping (upconverted to BF16)
        # For BF16 cache: always use global cache slots (no workspace)
        # prefill_workspace_starts has been adjusted in-place per chunk so
        # prefill indices automatically come out chunk-local
        topk_indices = triton_convert_req_index_to_global_index(
            attn_metadata.req_id_per_token,
            attn_metadata.block_table,
            topk_indices,
            BLOCK_SIZE=attn_metadata.block_size,
            NUM_TOPK_TOKENS=topk_indices.shape[1],
            HAS_PREFILL_WORKSPACE=has_prefill_workspace,
            prefill_workspace_request_ids=prefill_request_ids,
            prefill_workspace_starts=prefill_workspace_starts,
        )

        fp8_metadata = attn_metadata.fp8_extra_metadata
        assert isinstance(fp8_metadata, FlashMLASparseMetadata.FP8SeparatePrefillDecode)

        def _fp8_decode(q: torch.Tensor, topk_indices: torch.Tensor) -> torch.Tensor:
            # Reshape q: (num_decode_tokens, num_heads, head_dim)
            #         -> (num_decodes, seq_len, num_heads, head_dim)
            q = reshape_query_for_spec_decode(q, num_decodes)
            seq_len = q.shape[1]
            # Reshape topk_indices: (num_decode_tokens, topk)
            #                    -> (num_decodes, seq_len, topk)
            topk_indices = topk_indices.view(num_decodes, seq_len, -1)
            assert fp8_metadata.decode is not None
            attn_out, _ = self._fp8_flash_mla_kernel(
                q=q,
                kv_c_and_k_pe_cache=kv_c_and_k_pe_cache,
                topk_indices=topk_indices,
                kernel_metadata=fp8_metadata.decode.kernel_metadata,
            )
            # Reshape output: (num_decodes, seq_len, num_heads, head_dim_v)
            #              -> (num_decode_tokens, num_heads, head_dim_v)
            return reshape_attn_output_for_spec_decode(attn_out)

        num_decode_tokens = fp8_metadata.num_decode_tokens
        num_prefill_tokens = fp8_metadata.num_prefill_tokens

        # Pure decode: direct call without allocation
        if num_decode_tokens > 0 and num_prefill_tokens == 0:
            assert fp8_metadata.decode is not None
            attn_out = _fp8_decode(q, topk_indices)
        else:
            # Mixed or pure prefill: allocate output tensor
            attn_out = q.new_empty(
                (attn_metadata.num_actual_tokens, self.num_heads, self.kv_lora_rank),
                dtype=q.dtype,
                device=q.device,
            )

            if num_decode_tokens > 0:
                attn_out[:num_decode_tokens] = _fp8_decode(
                    q[:num_decode_tokens], topk_indices[:num_decode_tokens]
                )

            assert fp8_metadata.prefill is not None
            for chunk in fp8_metadata.prefill.chunks:
                chunk_workspace = self.prefill_bf16_workspace[: chunk.chunk_tot_seqlen]
                ops.cp_gather_and_upconvert_fp8_kv_cache(
                    kv_c_and_k_pe_cache,
                    chunk_workspace,
                    chunk.block_table,
                    chunk.seq_lens,
                    chunk.workspace_starts,
                    len(chunk.block_table),
                )

                chunk_q = q[chunk.tokens_slice]
                chunk_topk_indices_workspace = topk_indices[chunk.tokens_slice]

                attn_out[chunk.tokens_slice] = self._bf16_flash_mla_kernel(
                    chunk_q,
                    chunk_workspace,
                    chunk_topk_indices_workspace,
                )

        return attn_out