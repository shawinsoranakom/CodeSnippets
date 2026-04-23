def forward_cuda(
        self,
        x: torch.Tensor,
        scale: torch.Tensor | None = None,
        scale_ub: torch.Tensor | None = None,
        use_triton: bool = False,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        from vllm.model_executor.layers.quantization.utils import fp8_utils

        if (
            self.is_group_quant
            and self.use_ue8m0
            and self.use_deep_gemm_supported
            and (DeepGemmQuantScaleFMT.from_oracle() == DeepGemmQuantScaleFMT.UE8M0)
        ):
            return fp8_utils.per_token_group_quant_fp8_packed_for_deepgemm(
                x,
                group_size=self.group_size,
                use_ue8m0=True,
            )

        if self.is_group_quant and not self.static:
            assert scale is None, "Dynamic group quantization does not use scale"

            return fp8_utils.per_token_group_quant_fp8(
                x,
                group_size=self.group_size,
                column_major_scales=self.column_major_scales,
                tma_aligned_scales=self.tma_aligned_scales,
                dtype=_FP8_DTYPE,
                use_ue8m0=self.use_ue8m0,
            )

        assert (scale is not None) == self.static
        assert scale_ub is None or (
            not self.static
            and self.group_shape == GroupShape.PER_TOKEN
            and scale_ub.numel() == 1
        )

        return ops.scaled_fp8_quant(
            x,
            scale,
            num_token_padding=self.num_token_padding,
            scale_ub=scale_ub,
            use_per_token_if_dynamic=self.use_per_token_if_dynamic,
            group_shape=(self.group_shape.row, self.group_shape.col)
            if self.static
            else None,
        )