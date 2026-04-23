def h(self, x: torch.Tensor, base_out: torch.Tensor) -> torch.Tensor:
        """
        Additive bypass component for LoRA: h(x) = up(down(x)) * scale

        Note:
            Does not access original model weights - bypass mode is designed
            for quantized models where weights may not be accessible.

        Args:
            x: Input tensor
            base_out: Output from base forward (unused, for API consistency)

        Reference: LyCORIS functional/locon.py bypass_forward_diff
        """
        # FUNC_LIST: [None, None, F.linear, F.conv1d, F.conv2d, F.conv3d]
        FUNC_LIST = [None, None, F.linear, F.conv1d, F.conv2d, F.conv3d]

        v = self.weights
        # v[0]=up, v[1]=down, v[2]=alpha, v[3]=mid, v[4]=dora_scale, v[5]=reshape
        up = v[0]
        down = v[1]
        alpha = v[2]
        mid = v[3]

        # Compute scale = alpha / rank
        rank = down.shape[0]
        if alpha is not None:
            scale = alpha / rank
        else:
            scale = 1.0
        scale = scale * getattr(self, "multiplier", 1.0)

        # Cast dtype
        up = up.to(dtype=x.dtype)
        down = down.to(dtype=x.dtype)

        # Use module info from bypass injection, not weight dimension
        is_conv = getattr(self, "is_conv", False)
        conv_dim = getattr(self, "conv_dim", 0)
        kw_dict = getattr(self, "kw_dict", {})

        if is_conv:
            op = FUNC_LIST[
                conv_dim + 2
            ]  # conv_dim 1->conv1d(3), 2->conv2d(4), 3->conv3d(5)
            kernel_size = getattr(self, "kernel_size", (1,) * conv_dim)
            in_channels = getattr(self, "in_channels", None)

            # Reshape 2D weights to conv format using kernel_size
            # down: [rank, in_channels * prod(kernel_size)] -> [rank, in_channels, *kernel_size]
            # up: [out_channels, rank] -> [out_channels, rank, 1, 1, ...] (1x1 kernel)
            if down.dim() == 2:
                # down.shape[1] = in_channels * prod(kernel_size)
                if in_channels is not None:
                    down = down.view(down.shape[0], in_channels, *kernel_size)
                else:
                    # Fallback: assume 1x1 kernel if in_channels unknown
                    down = down.view(*down.shape, *([1] * conv_dim))
            if up.dim() == 2:
                # up always uses 1x1 kernel
                up = up.view(*up.shape, *([1] * conv_dim))
            if mid is not None:
                mid = mid.to(dtype=x.dtype)
                if mid.dim() == 2:
                    mid = mid.view(*mid.shape, *([1] * conv_dim))
        else:
            op = F.linear
            kw_dict = {}  # linear doesn't take stride/padding

        # Simple chain: down -> mid (if tucker) -> up
        if mid is not None:
            if not is_conv:
                mid = mid.to(dtype=x.dtype)
            hidden = op(x, down)
            hidden = op(hidden, mid, **kw_dict)
            out = op(hidden, up)
        else:
            hidden = op(x, down, **kw_dict)
            out = op(hidden, up)

        return out * scale