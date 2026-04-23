def forward_mqa(
        self,
        q: torch.Tensor | tuple[torch.Tensor, torch.Tensor],
        kv_c_and_k_pe_cache: torch.Tensor,
        attn_metadata: AiterMLAMetadata,
        layer: AttentionLayer,
    ) -> tuple[torch.Tensor, torch.Tensor | None]:
        assert kv_c_and_k_pe_cache.numel() > 0
        assert attn_metadata.decode is not None
        assert attn_metadata.decode.max_qo_len is not None

        if type(q) is tuple:
            q = torch.cat(q, dim=-1)

        assert isinstance(q, torch.Tensor)
        B = q.shape[0]

        if self._needs_head_repeat:
            q = q.repeat_interleave(self._head_repeat_factor, dim=1)
            kernel_num_heads = 16
        else:
            kernel_num_heads = self.num_heads

        o = torch.empty(
            B,
            kernel_num_heads,
            self.kv_lora_rank,
            dtype=attn_metadata.decode.attn_out_dtype,
            device=q.device,
        )

        kv_buffer = kv_c_and_k_pe_cache.unsqueeze(2)

        # Build kwargs for mla_decode_fwd. Pass persistent metadata only
        # when it was successfully computed (qseqlen=1 decode steps).
        # For multi-token verification steps (spec-dec), the kernel falls
        # back to computing metadata internally.
        mla_kwargs = dict(
            q_scale=layer._q_scale,
            kv_scale=layer._k_scale,
        )
        if attn_metadata.work_meta_data is not None:
            mla_kwargs.update(
                work_meta_data=attn_metadata.work_meta_data,
                work_indptr=attn_metadata.work_indptr,
                work_info_set=attn_metadata.work_info_set,
                reduce_indptr=attn_metadata.reduce_indptr,
                reduce_final_map=attn_metadata.reduce_final_map,
                reduce_partial_map=attn_metadata.reduce_partial_map,
            )

        rocm_aiter_ops.mla_decode_fwd(
            q,
            kv_buffer,
            o,
            self.scale,
            attn_metadata.decode.qo_indptr,
            attn_metadata.decode.max_qo_len,
            attn_metadata.decode.paged_kv_indptr,
            attn_metadata.decode.paged_kv_indices,
            attn_metadata.decode.paged_kv_last_page_len,
            **mla_kwargs,
        )

        if self._needs_head_repeat:
            o = o[:, :: self._head_repeat_factor, :]

        return o, None