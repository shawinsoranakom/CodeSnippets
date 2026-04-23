def _init(
        self,
        in_channels,
        out_channels,
        kernel_size,
        stride,
        padding,
        dilation,
        transposed,
        output_padding,
        groups,
        bias,
        padding_mode="zeros",
        device=None,
        dtype=None,
    ) -> None:
        factory_kwargs = {"device": device, "dtype": dtype}
        super().__init__()

        if out_channels <= 0:
            raise ValueError(f"out_channels must be greater than 0, got {out_channels}")
        if in_channels % groups != 0:
            raise ValueError("in_channels must be divisible by groups")
        if out_channels % groups != 0:
            raise ValueError("out_channels must be divisible by groups")
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.kernel_size = kernel_size
        self.stride = stride
        self.padding = padding
        self.dilation = dilation
        self.transposed = transposed
        self.output_padding = output_padding
        self.groups = groups
        if padding_mode not in _SUPPORTED_PADDING:
            raise ValueError(
                f"'padding_mode' {padding_mode} is not supported by quantized convolution"
            )
        self.padding_mode = padding_mode
        # Initialize as NCHW. set_weight will internally transpose to NHWC.
        if self.transposed:
            weight_shape = [in_channels, out_channels // self.groups]
        else:
            weight_shape = [out_channels, in_channels // self.groups]
        qweight = torch._empty_affine_quantized(
            weight_shape + list(kernel_size),
            scale=1,
            zero_point=0,
            dtype=torch.qint8,
            **{k: v for k, v in factory_kwargs.items() if k != "dtype"},
        )
        bias_float = (
            torch.zeros(
                out_channels,
                dtype=torch.float,
                **{k: v for k, v in factory_kwargs.items() if k != "dtype"},
            )
            if bias
            else None
        )

        self.set_weight_bias(qweight, bias_float)
        self.scale = 1.0
        self.zero_point = 0