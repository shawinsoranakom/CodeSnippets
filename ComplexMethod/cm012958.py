def from_float(cls, other):
        if type(other) is not cls._FLOAT_MODULE:
            raise AssertionError(
                f"Expected type {cls._FLOAT_MODULE}, got {type(other)}"
            )
        if not hasattr(other, "qconfig"):
            raise AssertionError("The float module must have 'qconfig'")
        # Setting the dropout to 0.0!
        observed = cls(
            other.embed_dim,
            other.num_heads,
            other.dropout,
            (other.in_proj_bias is not None),
            (other.bias_k is not None),
            other.add_zero_attn,
            other.kdim,
            other.vdim,
            other.batch_first,
        )
        observed.bias_k = other.bias_k
        observed.bias_v = other.bias_v
        observed.qconfig = other.qconfig

        # Set the linear weights
        # for the type: ignores, see https://github.com/pytorch/pytorch/issues/58969
        observed.out_proj.weight = other.out_proj.weight
        observed.out_proj.bias = other.out_proj.bias
        if other._qkv_same_embed_dim:
            # Use separate params
            bias = other.in_proj_bias
            _start = 0
            _end = _start + other.embed_dim
            weight = other.in_proj_weight[_start:_end, :]
            if bias is not None:
                bias = torch.nn.Parameter(bias[_start:_end], bias.requires_grad)
            observed.linear_Q.weight = torch.nn.Parameter(weight, weight.requires_grad)
            observed.linear_Q.bias = bias

            bias = other.in_proj_bias
            _start = _end
            _end = _start + other.embed_dim
            weight = other.in_proj_weight[_start:_end, :]
            if bias is not None:
                bias = torch.nn.Parameter(bias[_start:_end], bias.requires_grad)
            observed.linear_K.weight = torch.nn.Parameter(weight, weight.requires_grad)
            observed.linear_K.bias = bias

            bias = other.in_proj_bias
            _start = _end
            weight = other.in_proj_weight[_start:, :]
            if bias is not None:
                bias = torch.nn.Parameter(bias[_start:], bias.requires_grad)
            observed.linear_V.weight = torch.nn.Parameter(weight, weight.requires_grad)
            observed.linear_V.bias = bias
        else:
            observed.linear_Q.weight = nn.Parameter(other.q_proj_weight)
            observed.linear_K.weight = nn.Parameter(other.k_proj_weight)
            observed.linear_V.weight = nn.Parameter(other.v_proj_weight)
            if other.in_proj_bias is None:
                # pyrefly: ignore [bad-assignment]
                observed.linear_Q.bias = None
                # pyrefly: ignore [bad-assignment]
                observed.linear_K.bias = None
                # pyrefly: ignore [bad-assignment]
                observed.linear_V.bias = None
            else:
                observed.linear_Q.bias = nn.Parameter(
                    other.in_proj_bias[0 : other.embed_dim]
                )
                observed.linear_K.bias = nn.Parameter(
                    other.in_proj_bias[other.embed_dim : (other.embed_dim * 2)]
                )
                observed.linear_V.bias = nn.Parameter(
                    other.in_proj_bias[(other.embed_dim * 2) :]
                )
        observed.eval()
        # Explicit prepare
        observed = torch.ao.quantization.prepare(observed, inplace=True)
        return observed