def _sm100_cutlass_mla_decode(
        self,
        q_nope: torch.Tensor,
        q_pe: torch.Tensor,
        kv_c_and_k_pe_cache: torch.Tensor,
        seq_lens: torch.Tensor,
        page_table: torch.Tensor,
        workspace: torch.Tensor,
        sm_scale: float,
        num_kv_splits: int,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        assert q_nope.ndim == 3, f"q_nope must be a 3D tensor, but got {q_nope.ndim}"
        assert q_pe.ndim == 3, f"q_pe must be a 3D tensor, but got {q_pe.ndim}"
        assert kv_c_and_k_pe_cache.ndim == 3, (
            "kv_c_and_k_pe_cache must be a 3D tensor, but got {}".format(
                kv_c_and_k_pe_cache.ndim
            )
        )

        B_q, H, D_q_nope = q_nope.shape
        B_q_2, H_2, D_q_pe = q_pe.shape
        assert (B_q == B_q_2) and (H == H_2)

        _, PAGE_SIZE, D_ckv = kv_c_and_k_pe_cache.shape

        D_latent = 512
        D_rope = 64
        assert D_q_nope == D_latent
        assert D_q_pe == D_rope
        assert D_ckv == D_latent + D_rope

        MAX_HEADS = 128
        assert H <= MAX_HEADS, f"H must be <= {MAX_HEADS}, but got {H}"

        assert len(page_table.shape) == 2
        B_block_table, block_num = page_table.shape
        assert B_block_table == B_q
        assert block_num > 0, f"block num must be greater than 0, got {block_num}"
        assert block_num % (128 / PAGE_SIZE) == 0

        assert q_nope.dtype in (torch.float16, torch.bfloat16, torch.float8_e4m3fn), (
            f"q_nope.dtype needs to be fp16 or bf16 or e4m3 but got {q_nope.dtype}."
        )
        assert q_nope.dtype == q_pe.dtype == kv_c_and_k_pe_cache.dtype
        assert seq_lens.dtype == torch.int32, (
            f"seq_lens.dtype needs to be int32 but got {seq_lens.dtype}."
        )
        assert page_table.dtype == torch.int32, (
            f"page_table.dtype needs to be int32 but got {page_table.dtype}."
        )

        dtype = (
            torch.bfloat16
            if is_quantized_kv_cache(self.kv_cache_dtype)
            else q_nope.dtype
        )
        out = q_nope.new_empty((B_q, MAX_HEADS, D_latent), dtype=dtype)
        lse = (
            torch.empty((B_q, MAX_HEADS), dtype=torch.float32, device=q_nope.device)
            if self.need_to_return_lse_for_decode
            else torch.Tensor()
        )

        ops.sm100_cutlass_mla_decode(
            out,
            lse,
            q_nope,
            q_pe,
            kv_c_and_k_pe_cache,
            seq_lens,
            page_table,
            workspace,
            sm_scale,
            num_kv_splits,
        )

        if H < MAX_HEADS:
            # Extract the subsets of the outputs
            lse = lse[:, :H] if self.need_to_return_lse_for_decode else lse
            out = out[:, :H]

        return out, lse