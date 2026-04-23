def forward_custom(
        self,
        input: torch.Tensor,
        scale: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        if self.match_rocm_aiter:
            return self.forward_rocm_aiter(input, scale)

        result = torch.empty(
            input.shape, device=input.device, dtype=self.quant_key.dtype
        )

        if self.quant_key.scale.group_shape.is_per_group():
            # for tma_aligned, the scale must be passed to forward_custom
            # tma_aligned fusion then matches by custom op arguments
            if not self.is_tma_aligned:
                assert scale is None
                scale = self.make_scale(input, transposed=self.has_col_major_scales)

            finfo = torch.finfo(self.quant_key.dtype)
            fp8_min = finfo.min
            fp8_max = finfo.max

            _, result, scale = auto_functionalized(
                self.QUANT_OP,
                input=input,
                output_q=result,
                output_s=scale,
                group_size=self.quant_key.scale.group_shape[1],
                eps=1e-10,
                fp8_min=fp8_min,
                fp8_max=fp8_max,
                scale_ue8m0=self.is_e8m0,
                dummy_is_scale_transposed=self.has_col_major_scales,
                dummy_is_tma_aligned=self.is_tma_aligned,
            )
            return result, scale

        if self.quant_key.scale.static:
            assert scale is not None
            _, result = auto_functionalized(
                self.QUANT_OP, result=result, input=input, scale=scale
            )
            return result, scale
        else:
            assert scale is None
            scale = self.make_scale(input)
            _, result, scale = auto_functionalized(
                self.QUANT_OP, result=result, input=input, scale=scale, scale_ub=None
            )
            return result, scale