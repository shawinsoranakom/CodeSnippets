def __init__(
        self,
        dim,
        dim_out = None,
        mult = 4,
        no_bias = False,
        glu = True,
        use_conv = False,
        conv_kernel_size = 3,
        zero_init_output = True,
        dtype=None,
        device=None,
        operations=None,
    ):
        super().__init__()
        inner_dim = int(dim * mult)

        # Default to SwiGLU

        activation = nn.SiLU()

        dim_out = dim if dim_out is None else dim_out

        if glu:
            linear_in = GLU(dim, inner_dim, activation, dtype=dtype, device=device, operations=operations)
        else:
            linear_in = nn.Sequential(
                rearrange('b n d -> b d n') if use_conv else nn.Identity(),
                operations.Linear(dim, inner_dim, bias = not no_bias, dtype=dtype, device=device) if not use_conv else operations.Conv1d(dim, inner_dim, conv_kernel_size, padding = (conv_kernel_size // 2), bias = not no_bias, dtype=dtype, device=device),
                rearrange('b n d -> b d n') if use_conv else nn.Identity(),
                activation
            )

        linear_out = operations.Linear(inner_dim, dim_out, bias = not no_bias, dtype=dtype, device=device) if not use_conv else operations.Conv1d(inner_dim, dim_out, conv_kernel_size, padding = (conv_kernel_size // 2), bias = not no_bias, dtype=dtype, device=device)

        # # init last linear layer to 0
        # if zero_init_output:
        #     nn.init.zeros_(linear_out.weight)
        #     if not no_bias:
        #         nn.init.zeros_(linear_out.bias)


        self.ff = nn.Sequential(
            linear_in,
            rearrange('b d n -> b n d') if use_conv else nn.Identity(),
            linear_out,
            rearrange('b n d -> b d n') if use_conv else nn.Identity(),
        )