def _init_fp8_blockwise_common(
        self,
        M: int,
        N: int,
        K: int,
        device: str,
        helpers: ModuleType,
        block_m: int,
        block_k: int,
        scaling_type: ScalingType,
        use_padding: bool,
    ) -> None:
        """
        Common initialization for FP8 blockwise scaling.

        Args:
            block_m: Block size for M dimension (1 for 1x128, 128 for 128x128)
            block_k: Block size for K dimension (always 128)
            scaling_type: ScalingType enum value
            use_padding: If True, pad scales for 128x128; if False, use simple transpose for 1x128
        """
        self.float8_dtype = get_float8_dtype(self._float8_dtype_arg)

        # Validate SM90 support
        if device == "cuda" and torch.cuda.get_device_capability(0) != (9, 0):
            mode_name = "1x128" if block_m == 1 else "128x128"
            raise RuntimeError(
                f"FP8 BlockWise{mode_name} (DeepSeek style) scaling is only supported on CUDA SM90 (H100)."
            )

        # Validate dimension divisibility
        if block_m == 1:
            # 1x128 only requires K divisible by block_k
            if K % block_k != 0:
                raise RuntimeError(
                    f"FP8 BlockWise1x128 requires K divisible by {block_k}, got K={K}"
                )
        else:
            # 128x128 requires M, N, K all divisible by block size
            if (M % block_k) != 0 or (N % block_k) != 0 or (K % block_k) != 0:
                raise RuntimeError(
                    f"FP8 BlockWise128x128 requires M,N,K divisible by {block_k}, got M={M}, N={N}, K={K}"
                )

        # Create high-precision input tensors
        x_hp = torch.randn(
            M, K, device=device, dtype=self.base_dtype, requires_grad=self.auto_set()
        )
        y_hp = torch.randn(
            N, K, device=device, dtype=self.base_dtype, requires_grad=self.auto_set()
        )

        # Quantize to FP8 with block-wise scaling
        with torch.no_grad():
            x_lp, x_scales = helpers.tensor_to_scale_block(
                x_hp, self.float8_dtype, block_m, block_k
            )
            y_lp, y_scales = helpers.tensor_to_scale_block(
                y_hp, self.float8_dtype, block_m, block_k
            )
            x_lp = x_lp.detach().requires_grad_(self.auto_set())
            y_lp = y_lp.detach().requires_grad_(self.auto_set())

        # Process scales based on block configuration
        if use_padding:
            # 128x128: pad scales to multiple of 4, then transpose
            x_scales, _ = helpers._pad_128x128_scales(x_scales.detach())
            y_scales, _ = helpers._pad_128x128_scales(y_scales.detach())
            x_scales = x_scales.t()
            y_scales = y_scales.t()
        else:
            # 1x128: simple transpose to get "outer-dim-major" layout
            x_scales = x_scales.t().contiguous().t().detach()
            y_scales = y_scales.t().contiguous().t().detach()

        self.inputs = {
            "x": x_lp,
            "y": y_lp.t(),  # mat_b is (K, N)
            "scale_a": x_scales.reciprocal(),
            "scale_b": y_scales.reciprocal(),
        }
        self._set_scaled_mm_call_config(
            scale_recipe_a=scaling_type,
            scale_recipe_b=scaling_type,
        )