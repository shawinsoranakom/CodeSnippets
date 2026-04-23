def _scatter_mm6(
        blocks: torch.Tensor,
        others: torch.Tensor,
        c_indices: torch.Tensor,
        r_offsets: torch.Tensor,
        p_offsets: torch.Tensor,
        q_offsets: torch.Tensor,
        meta: dict,
        accumulators: torch.Tensor,
        force_contiguous: bool = True,
    ):
        SPLIT_N = meta["SPLIT_N"]
        _P, Ms, Ks = blocks.shape
        B, _K, N = others.shape
        B_, _M, N_ = accumulators.shape
        if N_ != N:
            raise AssertionError(f"accumulators N ({N_}) != others N ({N})")
        Ns = N // SPLIT_N
        if B_ != B:
            raise AssertionError(f"accumulators B ({B_}) != others B ({B})")

        def grid(META):
            return (
                r_offsets.shape[0] * B,
                triton.cdiv(Ms, META["TILE_M"]) * triton.cdiv(Ns, META["TILE_N"]),
            )

        dot_out_dtype = {
            torch.float16: tl.float32,
            torch.bfloat16: tl.float32,
            torch.float32: tl.float64,
            torch.float64: tl.float64,
        }[accumulators.dtype]
        if "allow_tf32" not in meta:
            meta.update(allow_tf32=dot_out_dtype == tl.float32)

        if c_indices.stride(0) != 1:
            raise AssertionError(
                f"c_indices.stride(0) must be 1, got {c_indices.stride(0)}"
            )
        if r_offsets.stride(0) != 1:
            raise AssertionError(
                f"r_offsets.stride(0) must be 1, got {r_offsets.stride(0)}"
            )
        if p_offsets.stride(0) != 1:
            raise AssertionError(
                f"p_offsets.stride(0) must be 1, got {p_offsets.stride(0)}"
            )
        if q_offsets.stride(0) != 1:
            raise AssertionError(
                f"q_offsets.stride(0) must be 1, got {q_offsets.stride(0)}"
            )

        # Re non-contiguous tensor arguments. Sometimes triton kernel
        # launches may fail with
        #
        #   RuntimeError: Triton Error [CUDA]: an illegal memory access was encountered
        #
        # that appears to be case when the size of a non-contiguous
        # tensor argument is larger than a certain threshold. Could
        # this be related to shared memory or L1 cache size of a GPU
        # card? In anycase, ensuring that tensor arguments are
        # contiguous seems to avoid the above exception. So, in the
        # following we'll always convert tensor arguments to
        # C-contiguous tensors.

        if force_contiguous:
            blocks = blocks.contiguous()
            others = others.contiguous()
            if not accumulators.is_contiguous():
                accumulators_ = accumulators.contiguous()
            else:
                accumulators_ = accumulators
        else:
            accumulators_ = accumulators

        _scatter_mm6_kernel[grid](
            B,
            Ms,
            Ks,
            N,
            blocks,
            blocks.stride(0),
            blocks.stride(1),
            blocks.stride(2),
            others,
            others.stride(0),
            others.stride(1),
            others.stride(2),
            accumulators_,
            accumulators_.stride(0),
            accumulators_.stride(1),
            accumulators_.stride(2),
            c_indices,
            r_offsets,
            p_offsets,
            q_offsets,
            dot_out_dtype=dot_out_dtype,
            **meta,
        )

        if force_contiguous and not accumulators.is_contiguous():
            accumulators.copy_(accumulators_)