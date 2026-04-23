def forward_impl(
        self,
        q: torch.Tensor,
        k_c_normed: torch.Tensor,  # key in unified attn
        k_pe: torch.Tensor,  # value in unified attn
        kv_cache: torch.Tensor,
        attn_metadata: "MLACommonMetadata",
        output: torch.Tensor,
        output_scale: torch.Tensor | None = None,
        output_block_scale: torch.Tensor | None = None,
        quant_group_size: int | None = None,
        quant_scale_ue8m0: bool | None = None,
        quant_col_major: bool | None = None,
        quant_tma_aligned: bool | None = None,
    ) -> torch.Tensor:
        assert output is not None, "Output tensor must be provided."

        quant_key = _detect_output_quant_key(
            output, output_scale, output_block_scale, self.num_heads * self.v_head_dim
        )
        if quant_key is not None:
            # The fusion pass has allocated output with quantized dtype
            # (FP8 or uint8 for FP4). We can't write into it directly,
            # so we swap in a temp buffer for computation, then quantize
            # into the real output at the end.
            # NOTE(carlyou): this is temporary until kernels support fp8 output
            quant_output = output
            output = torch.empty(
                output.shape[0],
                self.num_heads * self.v_head_dim,
                dtype=q.dtype,
                device=output.device,
            )

        if attn_metadata is None:
            # During the profile run try to simulate to worse case output size
            # for `self.kv_b_proj(kv_c_normed)` in `_compute_prefill_context`
            # since this can be large
            _ = torch.empty(
                (
                    self.chunked_prefill_workspace_size,
                    self.num_heads,
                    self.qk_nope_head_dim + self.v_head_dim,
                ),
                device=k_c_normed.device,
                dtype=k_c_normed.dtype,
            )

            # The zero fill is required when used with DP + EP
            # to ensure all ranks within a DP group compute the
            # same expert outputs.
            if quant_key is not None:
                return quant_output.fill_(0)
            return output.fill_(0)

        if self.impl.dcp_world_size == -1:
            self.impl.dcp_world_size = get_dcp_group().world_size

        fp8_attention = is_quantized_kv_cache(self.kv_cache_dtype)

        num_actual_toks = attn_metadata.num_actual_tokens

        # Inputs and outputs may be padded for CUDA graphs
        output_padded = output
        output = output[:num_actual_toks, ...]
        q = q[:num_actual_toks, ...]
        k_c_normed = k_c_normed[:num_actual_toks, ...]
        k_pe = k_pe[:num_actual_toks, ...]

        if fp8_attention and self.kv_cache_dtype != "fp8_ds_mla":
            kv_cache = kv_cache.view(current_platform.fp8_dtype())

        # Sparse MLA impls only support forward_mqa (decode-style attention)
        is_sparse_impl = isinstance(self.impl, SparseMLAAttentionImpl)

        if is_sparse_impl:
            num_mqa_tokens = q.size(0)
            num_mha_tokens = 0
        else:
            assert (
                attn_metadata.num_decodes is not None
                and attn_metadata.num_prefills is not None
                and attn_metadata.num_decode_tokens is not None
            )
            num_mqa_tokens = attn_metadata.num_decode_tokens
            num_mha_tokens = q.size(0) - num_mqa_tokens

        if num_mha_tokens > 0:
            self.impl.forward_mha(  # type: ignore[attr-defined]
                q[num_mqa_tokens:],
                k_c_normed[num_mqa_tokens:],
                k_pe[num_mqa_tokens:],
                kv_cache,
                attn_metadata,
                self._k_scale,
                output=output[num_mqa_tokens:],
            )

        if num_mqa_tokens > 0:
            mqa_q = q[:num_mqa_tokens]
            mqa_output_slice = output[:num_mqa_tokens]

            mqa_q_nope, mqa_q_pe = mqa_q.split(
                [self.qk_nope_head_dim, self.qk_rope_head_dim], dim=-1
            )

            # Convert from (B, N, P) to (N, B, P)
            mqa_q_nope = mqa_q_nope.transpose(0, 1)

            if self.q_pad_num_heads is not None:
                B, N, L = mqa_q_pe.shape
                mqa_pe_padded = mqa_q_pe.new_empty((B, self.q_pad_num_heads, L))
                mqa_pe_padded.resize_((B, N, L))
                mqa_pe_padded.copy_(mqa_q_pe)
                mqa_q_pe = mqa_pe_padded

            if self.is_aiter_triton_fp4_bmm_enabled:
                from aiter.ops.triton.batched_gemm_a16wfp4 import batched_gemm_a16wfp4

                mqa_ql_nope = batched_gemm_a16wfp4(
                    mqa_q_nope,
                    self.W_K,
                    self.W_K_scale,
                    transpose_bm=True,
                    prequant=True,
                    y_scale=self._q_scale if fp8_attention else None,
                )
            elif self.is_aiter_triton_fp8_bmm_enabled:
                # Multiply+Transpose (N, B, P)x(N, P, L)->(N, B, L)->(B, N, L)
                mqa_ql_nope = rocm_aiter_ops.triton_fp8_bmm(
                    mqa_q_nope,
                    self.W_K,
                    self.W_K_scale,
                    group_size=128,
                    transpose_bm=True,
                )
            else:
                # Pads the head_dim if necessary (for the underlying kernel)
                N, B, P = mqa_q_nope.shape
                _, _, L = self.W_UK_T.shape

                if self.q_pad_num_heads is not None:
                    mqa_ql_nope = mqa_q_nope.new_empty((self.q_pad_num_heads, B, L))
                    mqa_ql_nope.resize_((N, B, L))
                else:
                    mqa_ql_nope = mqa_q_nope.new_empty((N, B, L))

                # Multiply (N, B, P) x (N, P, L) -> (N, B, L)
                torch.bmm(mqa_q_nope, self.W_UK_T, out=mqa_ql_nope)

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
            if self.impl.dcp_world_size > 1:
                assert not fp8_attention, "DCP not support fp8 kvcache now."
                # concatenate mqa_ql_nope and mqa_q_pe -> (B, N, L + P)
                mqa_q = torch.cat(mqa_q, dim=-1)
                # mqa_q do allgather in head dim.
                mqa_q = get_dcp_group().all_gather(mqa_q, dim=1)

            # call decode attn
            if not is_sparse_impl:
                assert attn_metadata.decode is not None
            attn_out, lse = self.impl.forward_mqa(mqa_q, kv_cache, attn_metadata, self)  # type: ignore[attr-defined]

            # correct dcp attn_out with lse.
            if self.impl.dcp_world_size > 1:
                if self.dcp_a2a:
                    attn_out = dcp_a2a_lse_reduce(
                        attn_out,
                        lse,
                        get_dcp_group(),
                        is_lse_base_on_e=not getattr(self, "_use_fi_prefill", False),
                    )
                else:
                    attn_out = cp_lse_ag_out_rs(
                        attn_out,
                        lse,
                        get_dcp_group(),
                        is_lse_base_on_e=not getattr(self, "_use_fi_prefill", False),
                    )

            # v_up projection
            self._v_up_proj(attn_out, out=mqa_output_slice)

        if quant_key is not None:
            # Quantize the BF16 computation result into the quantized output
            actual = output[:num_actual_toks]
            if quant_key == kNvfp4Dynamic:
                # NVFP4: two FP4 values packed into one uint8
                assert output_block_scale is not None
                fp4_data, fp4_scales = ops.scaled_fp4_quant(actual, output_scale)
                quant_output[:num_actual_toks].copy_(fp4_data)
                output_block_scale[: fp4_scales.shape[0]].copy_(fp4_scales)
            elif quant_key in (kFp8Dynamic128Sym, kFp8Dynamic64Sym):
                # Per-group FP8
                assert output_block_scale is not None
                assert quant_group_size is not None, (
                    "Group FP8 output quant requested but "
                    "quant_group_size not passed through custom op"
                )
                finfo = torch.finfo(_FP8_DTYPE)
                torch.ops._C.per_token_group_fp8_quant(
                    actual,
                    quant_output[:num_actual_toks],
                    output_block_scale[:num_actual_toks],
                    quant_group_size,
                    1e-10,  # eps
                    finfo.min,
                    finfo.max,
                    quant_scale_ue8m0,
                    quant_col_major,
                    quant_tma_aligned,
                )
            elif quant_key == kFp8StaticTensorSym:
                # Static FP8 quantization
                fp8_data, _ = self._quant_fp8_op(actual, output_scale)
                quant_output[:num_actual_toks].copy_(fp8_data)
            else:
                raise ValueError(f"Unsupported quant_key: {quant_key}")
            return quant_output

        return output_padded