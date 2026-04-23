def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int | tuple[int, ...],
        stride: int | tuple[int, ...] = 1,
        padding: int | tuple[int, ...] | Literal["same", "valid"] = 0,
        dilation: int | tuple[int, ...] = 1,
        groups: int = 1,
        bias: bool = True,
        padding_mode: Literal["zeros", "reflect", "replicate", "circular"] = "zeros",
        *,
        params_dtype: torch.dtype | None = None,
    ) -> None:
        super().__init__()

        if params_dtype is None:
            params_dtype = torch.get_default_dtype()

        valid_padding_strings = {"same", "valid"}
        if isinstance(padding, str) and padding not in valid_padding_strings:
            raise ValueError(
                f"Invalid padding string '{padding}'. "
                f"Expected one of {valid_padding_strings}."
            )

        if padding == "same":
            padding = (
                kernel_size // 2
                if isinstance(kernel_size, int)
                else tuple(k // 2 for k in kernel_size)
            )
        elif padding == "valid":
            padding = 0

        kernel_size = (
            (kernel_size,) * self.num_dim
            if isinstance(kernel_size, int)
            else kernel_size
        )
        stride = (stride,) * self.num_dim if isinstance(stride, int) else stride
        padding = (padding,) * self.num_dim if isinstance(padding, int) else padding
        dilation = (dilation,) * self.num_dim if isinstance(dilation, int) else dilation

        if padding == "same" and any(s != 1 for s in stride):
            raise ValueError("padding='same' is not supported for strided convolutions")

        self.in_channels = in_channels
        self.out_channels = out_channels
        self.kernel_size = kernel_size
        self.stride = stride
        self.padding = padding
        self.dilation = dilation
        self.groups = groups
        self.padding_mode = padding_mode

        self.enable_linear = (
            (self.kernel_size == self.stride)
            and not any(self.padding)
            and self.groups == 1
        )
        self.input_size = in_channels * math.prod(self.kernel_size)

        self.weight = nn.Parameter(
            torch.empty(
                out_channels,
                in_channels // groups,
                *kernel_size,
                dtype=params_dtype,
            ),
        )

        if bias:
            self.bias = nn.Parameter(torch.empty(self.out_channels, dtype=params_dtype))
        else:
            self.register_parameter("bias", None)