def dequantize(self):
        r"""Utility to convert the quantized MHA back to float.

        The motivation for this is that it is not trivial to convert the weights
        from the format that is used in the quantized version back to the
        float.
        """
        fp = self._FLOAT_MODULE(
            self.embed_dim,
            self.num_heads,
            self.dropout,
            (self.linear_Q._weight_bias()[1] is not None),  # type: ignore[operator]
            (self.bias_k is not None),
            self.add_zero_attn,
            self.kdim,
            self.vdim,
            self.batch_first,
        )
        if fp._qkv_same_embed_dim != self._qkv_same_embed_dim:
            raise AssertionError(
                f"_qkv_same_embed_dim mismatch: {fp._qkv_same_embed_dim} != {self._qkv_same_embed_dim}"
            )
        if self.bias_k is not None:
            fp.bias_k = nn.Parameter(self.bias_k.dequantize())
        if self.bias_v is not None:
            fp.bias_v = nn.Parameter(self.bias_v.dequantize())

        # Set the linear weights
        # Note: Because the linear layers are quantized, mypy does not know how
        # to deal with them -- might need to ignore the typing checks.
        # for the type: ignore[has-type], see https://github.com/pytorch/pytorch/issues/58969
        w, b = self.out_proj._weight_bias()  # type: ignore[operator, has-type]
        fp.out_proj.weight = nn.Parameter(w.dequantize())
        if b is not None:
            fp.out_proj.bias = nn.Parameter(b)

        wQ, bQ = self.linear_Q._weight_bias()  # type: ignore[operator]
        wQ = wQ.dequantize()
        wK, bK = self.linear_K._weight_bias()  # type: ignore[operator]
        wK = wK.dequantize()
        wV, bV = self.linear_V._weight_bias()  # type: ignore[operator]
        wV = wV.dequantize()
        if fp._qkv_same_embed_dim:
            # Use separate params
            _start = 0
            _end = _start + fp.embed_dim
            fp.in_proj_weight[_start:_end, :] = wQ
            if fp.in_proj_bias is not None:
                # pyrefly: ignore [bad-argument-type]
                if not all(bQ == 0):
                    raise AssertionError("Expected all bQ elements to be 0")
                fp.in_proj_bias[_start:_end] = bQ

            _start = _end
            _end = _start + fp.embed_dim
            fp.in_proj_weight[_start:_end, :] = wK
            if fp.in_proj_bias is not None:
                # pyrefly: ignore [bad-argument-type]
                if not all(bK == 0):
                    raise AssertionError("Expected all bK elements to be 0")
                fp.in_proj_bias[_start:_end] = bK

            _start = _end
            fp.in_proj_weight[_start:, :] = wV
            if fp.in_proj_bias is not None:
                # pyrefly: ignore [bad-argument-type]
                if not all(bV == 0):
                    raise AssertionError("Expected all bV elements to be 0")
                fp.in_proj_bias[_start:] = bV
        else:
            fp.q_proj_weight = nn.Parameter(wQ)
            fp.k_proj_weight = nn.Parameter(wK)
            fp.v_proj_weight = nn.Parameter(wV)
            if fp.in_proj_bias is None:
                # pyrefly: ignore [bad-assignment]
                self.linear_Q.bias = None
                # pyrefly: ignore [bad-assignment]
                self.linear_K.bias = None
                # pyrefly: ignore [bad-assignment]
                self.linear_V.bias = None
            else:
                fp.in_proj_bias[0 : fp.embed_dim] = bQ
                fp.in_proj_bias[fp.embed_dim : (fp.embed_dim * 2)] = bK
                fp.in_proj_bias[(fp.embed_dim * 2) :] = bV

        return fp