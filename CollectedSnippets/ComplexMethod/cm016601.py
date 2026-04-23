def h(self, x: torch.Tensor, base_out: torch.Tensor) -> torch.Tensor:
        """
        Additive bypass component for LoKr: efficient Kronecker product application.

        Note:
            Does not access original model weights - bypass mode is designed
            for quantized models where weights may not be accessible.

        Args:
            x: Input tensor
            base_out: Output from base forward (unused, for API consistency)

        Reference: LyCORIS functional/lokr.py bypass_forward_diff
        """
        # FUNC_LIST: [None, None, F.linear, F.conv1d, F.conv2d, F.conv3d]
        FUNC_LIST = [None, None, F.linear, F.conv1d, F.conv2d, F.conv3d]

        v = self.weights
        # v[0]=w1, v[1]=w2, v[2]=alpha, v[3]=w1_a, v[4]=w1_b, v[5]=w2_a, v[6]=w2_b, v[7]=t2, v[8]=dora
        w1 = v[0]
        w2 = v[1]
        alpha = v[2]
        w1_a = v[3]
        w1_b = v[4]
        w2_a = v[5]
        w2_b = v[6]
        t2 = v[7]

        use_w1 = w1 is not None
        use_w2 = w2 is not None
        tucker = t2 is not None

        # Use module info from bypass injection, not weight dimension
        is_conv = getattr(self, "is_conv", False)
        conv_dim = getattr(self, "conv_dim", 0)
        kw_dict = getattr(self, "kw_dict", {}) if is_conv else {}

        if is_conv:
            op = FUNC_LIST[conv_dim + 2]
        else:
            op = F.linear

        # Determine rank and scale
        rank = w1_b.size(0) if not use_w1 else w2_b.size(0) if not use_w2 else alpha
        scale = (alpha / rank if alpha is not None else 1.0) * getattr(
            self, "multiplier", 1.0
        )

        # Build c (w1)
        if use_w1:
            c = w1.to(dtype=x.dtype)
        else:
            c = w1_a.to(dtype=x.dtype) @ w1_b.to(dtype=x.dtype)
        uq = c.size(1)

        # Build w2 components
        if use_w2:
            ba = w2.to(dtype=x.dtype)
        else:
            a = w2_b.to(dtype=x.dtype)
            b = w2_a.to(dtype=x.dtype)
            if is_conv:
                if tucker:
                    # Tucker: a, b get 1s appended (kernel is in t2)
                    if a.dim() == 2:
                        a = a.view(*a.shape, *([1] * conv_dim))
                    if b.dim() == 2:
                        b = b.view(*b.shape, *([1] * conv_dim))
                else:
                    # Non-tucker conv: b may need 1s appended
                    if b.dim() == 2:
                        b = b.view(*b.shape, *([1] * conv_dim))

        # Reshape input by uq groups
        if is_conv:
            B, _, *rest = x.shape
            h_in_group = x.reshape(B * uq, -1, *rest)
        else:
            h_in_group = x.reshape(*x.shape[:-1], uq, -1)

        # Apply w2 path
        if use_w2:
            hb = op(h_in_group, ba, **kw_dict)
        else:
            if is_conv:
                if tucker:
                    t = t2.to(dtype=x.dtype)
                    if t.dim() == 2:
                        t = t.view(*t.shape, *([1] * conv_dim))
                    ha = op(h_in_group, a)
                    ht = op(ha, t, **kw_dict)
                    hb = op(ht, b)
                else:
                    ha = op(h_in_group, a, **kw_dict)
                    hb = op(ha, b)
            else:
                ha = op(h_in_group, a)
                hb = op(ha, b)

        # Reshape and apply c (w1)
        if is_conv:
            hb = hb.view(B, -1, *hb.shape[1:])
            h_cross_group = hb.transpose(1, -1)
        else:
            h_cross_group = hb.transpose(-1, -2)

        hc = F.linear(h_cross_group, c)

        if is_conv:
            hc = hc.transpose(1, -1)
            out = hc.reshape(B, -1, *hc.shape[3:])
        else:
            hc = hc.transpose(-1, -2)
            out = hc.reshape(*hc.shape[:-2], -1)

        return out * scale