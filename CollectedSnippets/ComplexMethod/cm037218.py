def forward_mqa(
        self,
        q: torch.Tensor | tuple[torch.Tensor, torch.Tensor],
        kv_c_and_k_pe_cache: torch.Tensor,
        attn_metadata: FlashMLAMetadata,
        layer: AttentionLayer,
    ) -> tuple[torch.Tensor, torch.Tensor | None]:
        # TODO: (zyongye) decode function for mla here
        assert kv_c_and_k_pe_cache.numel() > 0
        assert attn_metadata.decode is not None

        if type(q) is tuple:
            q = torch.cat(q, dim=-1)

        # mypy assertion: q is now always a tensor
        assert isinstance(q, torch.Tensor)

        num_decodes = attn_metadata.num_decodes
        q = reshape_query_for_spec_decode(q, num_decodes)

        scheduler_metadata = attn_metadata.decode.scheduler_metadata
        if envs.VLLM_BATCH_INVARIANT and not is_quantized_kv_cache(self.kv_cache_dtype):
            device = q.device
            dtype = torch.int32

            B = q.shape[0]
            # block_table shape: [batch_size, max_num_blocks_per_seq]
            # The number of blocks per sequence is in the second dimension
            topk = attn_metadata.decode.block_table.shape[-1]
            B_TOPK = 64
            assert topk % B_TOPK == 0, f"topk ({topk}) must be divisible by {B_TOPK}"
            end_block_idx = topk // B_TOPK

            # Single partition => num_sm_parts = 1
            # TileSchedulerMetaDataSize = 8, layout:
            # [begin_idx, begin_block_idx, end_idx, end_block_idx,
            #  begin_n_split_idx, _, _, _]
            tile_scheduler_metadata = torch.zeros((1, 8), dtype=dtype, device=device)
            tile_scheduler_metadata[0, 0] = 0  # begin_idx
            tile_scheduler_metadata[0, 1] = 0  # sched_begin_block_idx
            tile_scheduler_metadata[0, 2] = B - 1  # end_idx
            tile_scheduler_metadata[0, 3] = end_block_idx
            tile_scheduler_metadata[0, 4] = 0  # begin_n_split_idx
            # fields [5..7] stay 0

            # Non-split path ignores num_splits, but the API requires it:
            # zeros of length B+1
            num_splits = torch.zeros((B + 1,), dtype=dtype, device=device)
            scheduler_metadata.tile_scheduler_metadata = tile_scheduler_metadata
            scheduler_metadata.num_splits = num_splits

        if is_quantized_kv_cache(self.kv_cache_dtype):
            o, lse = flash_mla_with_kvcache_fp8(
                q=q,
                k_cache=kv_c_and_k_pe_cache.unsqueeze(-2),  # Add head dim of 1
                block_table=attn_metadata.decode.block_table,
                cache_seqlens=attn_metadata.decode.seq_lens,
                head_dim_v=self.kv_lora_rank,
                tile_scheduler_metadata=scheduler_metadata.tile_scheduler_metadata,
                num_splits=scheduler_metadata.num_splits,
                softmax_scale=self.scale,
                causal=True,
                descale_q=layer._q_scale.reshape(1),
                descale_k=layer._k_scale.reshape(1),
            )
        else:
            o, lse = flash_mla_with_kvcache(
                q=q,
                k_cache=kv_c_and_k_pe_cache.unsqueeze(-2),  # Add head dim of 1
                block_table=attn_metadata.decode.block_table,
                cache_seqlens=attn_metadata.decode.seq_lens,
                head_dim_v=self.kv_lora_rank,
                tile_scheduler_metadata=scheduler_metadata,
                softmax_scale=self.scale,
                causal=True,
                is_fp8_kvcache=False,
            )

        o = reshape_attn_output_for_spec_decode(o)

        return o, lse