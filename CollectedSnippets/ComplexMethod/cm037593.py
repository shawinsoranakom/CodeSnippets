def forward_native(
        self, x: torch.Tensor, z: torch.Tensor | None = None
    ) -> torch.Tensor:
        """
        Native PyTorch implementation of RMS normalization with gating.

        Args:
            x: Input tensor
            z: Optional gating tensor

        Returns:
            Normalized (and optionally gated) tensor

        If z is not None:
            - norm_before_gate=True: out = norm(x) * silu(z)
            - norm_before_gate=False: out = norm(x * silu(z))
        """
        orig_dtype = x.dtype
        x = x.float()
        weight = self.weight.float()
        z = z.float() if z is not None else None

        assert self.activation in ["silu", "sigmoid", "swish"]
        act_fn = F.sigmoid if self.activation == "sigmoid" else F.silu

        # Apply gating before normalization if needed
        if z is not None and not self.norm_before_gate:
            x = x * act_fn(z)

        # RMS Normalization
        if self.group_size is None:
            # Standard RMS norm across the last dimension
            variance = x.pow(2).mean(dim=-1, keepdim=True)
            x_normed = x * torch.rsqrt(variance + self.eps)
            out = x_normed * weight
        else:
            # Group RMS norm
            from einops import rearrange

            x_group = rearrange(x, "... (g d) -> ... g d", d=self.group_size)
            variance = x_group.pow(2).mean(dim=-1, keepdim=True)
            x_normed = x_group * torch.rsqrt(variance + self.eps)
            out = rearrange(x_normed, "... g d -> ... (g d)") * weight

        # Apply gating after normalization if needed
        if z is not None and self.norm_before_gate:
            out = out * act_fn(z)

        return out.to(orig_dtype)