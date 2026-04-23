def _continuation_prefill(
        self,
        layer: Any,
        query: torch.Tensor,  # (q_len, Hq, D)
        key_chunk: torch.Tensor,  # (q_len, Hk, D)
        val_chunk: torch.Tensor,  # (q_len, Hk, D)
        kv_cache: torch.Tensor,  # (num_blocks, block_size, Hk, slot_size)
        block_table: torch.Tensor,  # (1, max_num_blocks)
        cached_len: int,
        seq_len: int,
        Pi: torch.Tensor,
        centroids: torch.Tensor,
    ) -> torch.Tensor:
        """Handle continuation chunk by dequanting cached K/V from TQ cache.

        Dequants previously cached K/V, concatenates with the current
        chunk's raw K/V, then runs flash_attn with causal masking.
        """
        q_len, Hq, D = query.shape
        Hk = key_chunk.shape[1]
        device = query.device
        block_size = kv_cache.shape[1]
        BLOCK_D = triton.next_power_of_2(D)

        mse_bytes = self._mse_bytes
        val_data_bytes = self._val_data_bytes

        # Dequant cached K/V from TQ cache
        # Allocate slightly over to align to block_size for the grid.
        # Reuse cached buffers to avoid per-call allocation (~16MB at 8K).
        alloc_len = math.ceil(cached_len / block_size) * block_size
        buf_shape = (1, Hk, alloc_len, D)
        k_buf = getattr(layer, "_tq_k_dequant_buf", None)
        if k_buf is None or k_buf.shape[2] < alloc_len:
            k_buf = torch.empty(buf_shape, dtype=torch.float16, device=device)
            v_buf = torch.empty(buf_shape, dtype=torch.float16, device=device)
            layer._tq_k_dequant_buf = k_buf
            layer._tq_v_dequant_buf = v_buf
        else:
            v_buf = layer._tq_v_dequant_buf
        k_cached = k_buf[:, :, :alloc_len, :].zero_()
        v_cached = v_buf[:, :, :alloc_len, :].zero_()

        grid = (alloc_len, 1 * Hk)
        _tq_full_dequant_kv[grid](
            kv_cache,
            block_table,
            centroids,
            k_cached,
            v_cached,
            k_cached.stride(0),
            k_cached.stride(1),
            k_cached.stride(2),
            v_cached.stride(0),
            v_cached.stride(1),
            v_cached.stride(2),
            kv_cache.stride(0),
            kv_cache.stride(1),
            kv_cache.stride(2),
            block_table.stride(0),
            HEAD_DIM=D,
            BLOCK_SIZE=block_size,
            NUM_KV_HEADS=Hk,
            MSE_BYTES=mse_bytes,
            KPS=self.tq_config.key_packed_size,
            VQB=self.tq_config.effective_value_quant_bits,
            VAL_DATA_BYTES=val_data_bytes,
            MSE_BITS=self.tq_config.key_mse_bits,
            KEY_FP8=1 if self.tq_config.key_fp8 else 0,
            BLOCK_D=BLOCK_D,
            NORM_CORRECTION=1 if self.tq_config.norm_correction else 0,
            FP8_E4B15=_use_fp8_e4b15(device.index or 0),
            num_warps=4,
        )

        # Inverse-rotate MSE keys back to original space
        if not self.tq_config.key_fp8:
            k_flat = k_cached[0, :, :cached_len, :].reshape(-1, D).float()
            k_flat = k_flat @ Pi
            k_cached_trim = (
                k_flat.to(torch.float16).reshape(Hk, cached_len, D).transpose(0, 1)
            )  # (cached_len, Hk, D)
        else:
            k_cached_trim = (
                k_cached[0, :, :cached_len, :].transpose(0, 1).contiguous()
            )  # (cached_len, Hk, D)

        v_cached_trim = (
            v_cached[0, :, :cached_len, :].transpose(0, 1).contiguous()
        )  # (cached_len, Hk, D)

        # Concatenate cached + current chunk K/V (match query dtype)
        qdtype = query.dtype
        k_full = torch.cat([k_cached_trim.to(qdtype), key_chunk], dim=0)
        v_full = torch.cat([v_cached_trim.to(qdtype), val_chunk], dim=0)

        # Attention: q_len queries attending to seq_len K/V with causal mask
        if _HAS_FLASH_ATTN:
            cu_seqlens_q = torch.tensor([0, q_len], device=device, dtype=torch.int32)
            cu_seqlens_k = torch.tensor([0, seq_len], device=device, dtype=torch.int32)
            return flash_attn_varlen_func(
                q=query,
                k=k_full,
                v=v_full,
                cu_seqlens_q=cu_seqlens_q,
                cu_seqlens_k=cu_seqlens_k,
                max_seqlen_q=q_len,
                max_seqlen_k=seq_len,
                softmax_scale=self.scale,
                causal=True,
            )
        else:
            # SDPA fallback: expand KV for GQA, build causal mask
            q_t = query.transpose(0, 1).unsqueeze(0)  # (1, Hq, q_len, D)
            k_t = k_full.transpose(0, 1).unsqueeze(0)  # (1, Hk, seq_len, D)
            v_t = v_full.transpose(0, 1).unsqueeze(0)  # (1, Hk, seq_len, D)
            # Build causal mask: query position p can attend to K position j
            # where j <= cached_len + p (p is 0-indexed within chunk)
            q_pos = torch.arange(q_len, device=device).unsqueeze(1) + cached_len
            k_pos = torch.arange(seq_len, device=device).unsqueeze(0)
            mask = k_pos <= q_pos  # (q_len, seq_len)
            out = F.scaled_dot_product_attention(
                q_t,
                k_t,
                v_t,
                attn_mask=mask,
                scale=self.scale,
                enable_gqa=(Hk < Hq),
            )  # (1, Hq, q_len, D)
            return out[0].transpose(0, 1)