def h(self, x: torch.Tensor, base_out: torch.Tensor) -> torch.Tensor:
        """
        Additive bypass component for LoRA training: h(x) = up(down(x)) * scale

        Simple implementation using the nn.Module weights directly.
        No mid/dora/reshape branches (create_train doesn't create them).

        Args:
            x: Input tensor
            base_out: Output from base forward (unused, for API consistency)
        """
        # Compute scale = alpha / rank * multiplier
        scale = (self.alpha / self.rank) * getattr(self, "multiplier", 1.0)

        # Get module info from bypass injection
        is_conv = getattr(self, "is_conv", False)
        conv_dim = getattr(self, "conv_dim", 0)
        kw_dict = getattr(self, "kw_dict", {})

        # Get weights (keep in original dtype for numerical stability)
        down_weight = self.lora_down.weight
        up_weight = self.lora_up.weight

        if is_conv:
            # Conv path: use functional conv
            # conv_dim: 1=conv1d, 2=conv2d, 3=conv3d
            conv_fn = (F.conv1d, F.conv2d, F.conv3d)[conv_dim - 1]

            # Reshape 2D weights to conv format if needed
            # down: [rank, in_features] -> [rank, in_channels, *kernel_size]
            # up: [out_features, rank] -> [out_features, rank, 1, 1, ...]
            if down_weight.dim() == 2:
                kernel_size = getattr(self, "kernel_size", (1,) * conv_dim)
                in_channels = getattr(self, "in_channels", None)
                if in_channels is not None:
                    down_weight = down_weight.view(
                        down_weight.shape[0], in_channels, *kernel_size
                    )
                else:
                    # Fallback: assume 1x1 kernel
                    down_weight = down_weight.view(
                        *down_weight.shape, *([1] * conv_dim)
                    )
            if up_weight.dim() == 2:
                # up always uses 1x1 kernel
                up_weight = up_weight.view(*up_weight.shape, *([1] * conv_dim))

            # down conv uses stride/padding from module, up is 1x1
            hidden = conv_fn(x, down_weight, **kw_dict)

            # mid layer if exists (tucker decomposition)
            if self.lora_mid is not None:
                mid_weight = self.lora_mid.weight
                if mid_weight.dim() == 2:
                    mid_weight = mid_weight.view(*mid_weight.shape, *([1] * conv_dim))
                hidden = conv_fn(hidden, mid_weight)

            # up conv is always 1x1 (no stride/padding)
            out = conv_fn(hidden, up_weight)
        else:
            # Linear path: simple matmul chain
            hidden = F.linear(x, down_weight)

            # mid layer if exists
            if self.lora_mid is not None:
                mid_weight = self.lora_mid.weight
                hidden = F.linear(hidden, mid_weight)

            out = F.linear(hidden, up_weight)

        return out * scale