def forward_cuda(
        self,
        x: torch.Tensor,
        residual: torch.Tensor | None = None,
    ) -> torch.Tensor | tuple[torch.Tensor, torch.Tensor]:
        if residual is None and not envs.VLLM_BATCH_INVARIANT:
            return ir.ops.rms_norm(
                x, self.weight.data, self.variance_epsilon, self.variance_size_override
            )

        if self.variance_size_override is not None:
            return self.forward_native(x, residual)

        # Optional Oink SM100 fast path (fused residual-add + RMSNorm, in-place).
        # This mirrors vLLM's fused_add_rms_norm semantics by mutating both
        # `x` (normalized output) and `residual` (residual-out buffer).
        if (
            residual is not None
            and getattr(self, "_use_oink_fused_add_rmsnorm", False)
            and x.is_cuda
            and residual.is_cuda
            and x.shape == residual.shape
            and x.dtype == residual.dtype
            and x.dim() >= 2
            and self.has_weight
            and not envs.VLLM_BATCH_INVARIANT
            and self.weight.data.dtype == x.dtype
            and self.weight.data.is_contiguous()
        ):
            orig_shape = x.shape
            hidden_size = orig_shape[-1]
            if _can_view_as_2d(x) and _can_view_as_2d(residual):
                x_2d = x.view(-1, hidden_size)
                res_2d = residual.view(-1, hidden_size)

                # The Oink in-place pointer path supports the common vLLM
                # layout where:
                # - `x` may be strided/padded row-major (stride(1) == 1), and
                # - `residual` is contiguous row-major ([M, N] with stride(0) == N).
                # If these conditions are not met, fall back to vLLM's built-in
                # fused kernel.
                if (
                    _is_oink_stride_compatible_2d(x_2d)
                    and _is_oink_stride_compatible_2d(res_2d)
                    and res_2d.is_contiguous()
                ):
                    _oink_ops.fused_add_rms_norm_(
                        x_2d,
                        res_2d,
                        self.weight.data,
                        self.variance_epsilon,
                    )
                    return x, residual

        if residual is not None:
            return fused_add_rms_norm(
                x, residual, self.weight.data, self.variance_epsilon
            )
        else:
            assert envs.VLLM_BATCH_INVARIANT
            return rms_norm_batch_invariant(x, self.weight.data, self.variance_epsilon)