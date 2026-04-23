def forward_mqa(
        self,
        q: torch.Tensor | tuple[torch.Tensor, torch.Tensor],
        kv_c_and_k_pe_cache: torch.Tensor,
        attn_metadata: MLACommonMetadata,
        layer: AttentionLayer,
    ) -> tuple[torch.Tensor, torch.Tensor | None]:
        assert kv_c_and_k_pe_cache.numel() > 0
        assert attn_metadata.decode is not None

        if isinstance(q, tuple):
            q_nope, q_pe = q
            q = torch.cat([q_nope, q_pe], dim=-1)

        # trtllm API requires extra dimension q_len_per_request for MTP
        if attn_metadata.num_decode_tokens % attn_metadata.num_decodes != 0:
            logger.warning_once(
                """FlashInferMLAImpl got a query of uneven length.
                This usually indicates an issue in batch reordering
                or incorrect setup in dummy_run."""
            )
            q = q.unsqueeze(1)
        else:
            q = q.view(attn_metadata.num_decodes, -1, q.shape[-2], q.shape[-1])

        if self.bmm1_scale is None:
            self.bmm1_scale = self.scale
            if is_quantized_kv_cache(self.kv_cache_dtype):
                self.bmm1_scale *= layer._q_scale_float * layer._k_scale_float

        if self.bmm2_scale is None:
            self.bmm2_scale = 1.0
            if is_quantized_kv_cache(self.kv_cache_dtype):
                self.bmm2_scale *= layer._k_scale_float

        o = trtllm_batch_decode_with_kv_cache_mla(
            query=q,
            kv_cache=kv_c_and_k_pe_cache.unsqueeze(1),
            workspace_buffer=self._workspace_buffer,
            qk_nope_head_dim=self.qk_nope_head_dim,
            kv_lora_rank=self.kv_lora_rank,
            qk_rope_head_dim=self.qk_rope_head_dim,
            block_tables=attn_metadata.decode.block_table,
            seq_lens=attn_metadata.decode.seq_lens,
            max_seq_len=attn_metadata.max_seq_len,
            bmm1_scale=self.bmm1_scale,
            bmm2_scale=self.bmm2_scale,
        )

        # Flatten the output for consistent shape
        o = o.view(-1, o.shape[-2], o.shape[-1])

        # TODO: Return LSE pending support from Flashinfer API:
        # https://github.com/flashinfer-ai/flashinfer/pull/1566
        return o, None