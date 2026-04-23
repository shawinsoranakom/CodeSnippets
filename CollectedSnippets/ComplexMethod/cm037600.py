def forward_hip(
        self,
        x: torch.Tensor,
        scale: torch.Tensor | None = None,
        scale_ub: torch.Tensor | None = None,
        use_triton: bool = False,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        if self.is_group_quant and use_triton:
            assert scale is None, "Dynamic group quantization does not use scale"

            return torch.ops.vllm.triton_per_token_group_quant_fp8(x, self.group_size)

        use_aiter_quant = self.use_aiter and scale_ub is None and x.is_contiguous()
        use_aiter_per_tensor_quant = (
            use_aiter_quant and self.group_shape.is_per_tensor()
        )
        use_aiter_per_token_quant = use_aiter_quant and self.group_shape.is_per_token()

        use_aiter_per_group_quant = use_aiter_quant and self.group_shape.is_per_group()

        if use_aiter_per_group_quant:
            return rocm_aiter_ops.group_fp8_quant(x, self.group_size)
        if use_aiter_per_tensor_quant:
            return rocm_aiter_ops.per_tensor_quant(x, _FP8_DTYPE, scale)
        if use_aiter_per_token_quant:
            return rocm_aiter_ops.per_token_quant(x, _FP8_DTYPE, scale)

        # Fallback to native implementation for group quantization.
        if self.is_group_quant:
            assert scale is None, "Dynamic group quantization does not use scale"
            return self._quantize_group_native(x)

        # Fallback to CUDA implementation
        return self.forward_cuda(x, scale, scale_ub)