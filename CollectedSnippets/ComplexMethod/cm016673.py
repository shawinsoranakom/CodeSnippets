def __init__(
        self,
        in_channels,
        out_channels,
        kernel_size,
        stride: Union[int, Tuple[int, int, int]] = 1,
        padding: Union[int, Tuple[int, int, int]] = 0,
        dilation: Union[int, Tuple[int, int, int]] = 1,
        groups=1,
        bias=True,
        padding_mode="zeros",
    ):
        super(DualConv3d, self).__init__()

        self.in_channels = in_channels
        self.out_channels = out_channels
        self.padding_mode = padding_mode
        # Ensure kernel_size, stride, padding, and dilation are tuples of length 3
        if isinstance(kernel_size, int):
            kernel_size = (kernel_size, kernel_size, kernel_size)
        if kernel_size == (1, 1, 1):
            raise ValueError(
                "kernel_size must be greater than 1. Use make_linear_nd instead."
            )
        if isinstance(stride, int):
            stride = (stride, stride, stride)
        if isinstance(padding, int):
            padding = (padding, padding, padding)
        if isinstance(dilation, int):
            dilation = (dilation, dilation, dilation)

        # Set parameters for convolutions
        self.groups = groups
        self.bias = bias

        # Define the size of the channels after the first convolution
        intermediate_channels = (
            out_channels if in_channels < out_channels else in_channels
        )

        # Define parameters for the first convolution
        self.weight1 = nn.Parameter(
            torch.Tensor(
                intermediate_channels,
                in_channels // groups,
                1,
                kernel_size[1],
                kernel_size[2],
            )
        )
        self.stride1 = (1, stride[1], stride[2])
        self.padding1 = (0, padding[1], padding[2])
        self.dilation1 = (1, dilation[1], dilation[2])
        if bias:
            self.bias1 = nn.Parameter(torch.Tensor(intermediate_channels))
        else:
            self.register_parameter("bias1", None)

        # Define parameters for the second convolution
        self.weight2 = nn.Parameter(
            torch.Tensor(
                out_channels, intermediate_channels // groups, kernel_size[0], 1, 1
            )
        )
        self.stride2 = (stride[0], 1, 1)
        self.padding2 = (padding[0], 0, 0)
        self.dilation2 = (dilation[0], 1, 1)
        if bias:
            self.bias2 = nn.Parameter(torch.Tensor(out_channels))
        else:
            self.register_parameter("bias2", None)

        # Initialize weights and biases
        self.reset_parameters()