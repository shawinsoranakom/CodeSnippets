def forward_native(
        self,
        x: torch.Tensor,
        scale: torch.Tensor | None = None,
        scale_ub: torch.Tensor | None = None,
        use_triton: bool = False,
    ):
        if self.is_group_quant and not self.static:
            assert scale is None, "Dynamic group quantization does not use scale"
            return self._quantize_group_native(x)

        assert (scale is not None) == self.static
        assert scale_ub is None or (
            not self.static
            and self.group_shape == GroupShape.PER_TOKEN
            and scale_ub.numel() == 1
        )

        if scale is None:
            if self.group_shape == GroupShape.PER_TOKEN:
                x_max, _ = x.abs().max(dim=-1)
                x_max = x_max.unsqueeze(-1).to(torch.float32)
                if scale_ub is not None:
                    x_max = x_max.clamp(max=scale_ub)
            else:
                x_max = x.abs().max().unsqueeze(-1).to(torch.float32)

            scale = (x_max / _FP8_MAX).clamp(min=_FP8_MIN_SCALING_FACTOR)
        else:
            scale = prep_scale_for_group_broadcast(scale, x, self.group_shape)

        # Even for dynamic per-token scales,
        # reciprocal performs slightly better than division
        out = (
            x.to(torch.float32)
            * group_broadcast(scale.to(torch.float32), x.shape[-2:]).reciprocal()
        )
        out = out.clamp(_FP8_MIN, _FP8_MAX).to(_FP8_DTYPE)

        # This currently generates an extra Triton kernel in compilation.
        # Fortunately, we don't use padding if compiling.
        # TODO(luka): benchmark torch._scaled_mm to hopefully remove padding
        #  in general.
        if self.num_token_padding is not None:
            padding = max(self.num_token_padding - out.size(0), 0)
            out = F.pad(out, (0, 0, 0, padding), "constant", 0.0)

        return out, scale