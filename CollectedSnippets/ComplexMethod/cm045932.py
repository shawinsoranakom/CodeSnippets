def __init__(
        self,
        num_channels,
        num_filters,
        filter_size,
        stride=1,
        groups=1,
        act=None,
        is_repped=False,
        single_init=False,
        **kwargs,
    ):
        super().__init__()

        padding = (filter_size - 1) // 2
        dilation = 1

        in_channels = num_channels
        out_channels = num_filters
        kernel_size = filter_size
        internal_channels_1x1_3x3 = None
        nonlinear = act

        self.is_repped = is_repped

        if nonlinear is None:
            self.nonlinear = nn.Identity()
        else:
            self.nonlinear = nn.ReLU()

        self.kernel_size = kernel_size
        self.out_channels = out_channels
        self.groups = groups
        assert padding == kernel_size // 2

        if is_repped:
            self.dbb_reparam = nn.Conv2d(
                in_channels=in_channels,
                out_channels=out_channels,
                kernel_size=kernel_size,
                stride=stride,
                padding=padding,
                dilation=dilation,
                groups=groups,
                bias=True,
            )
        else:
            self.dbb_origin = conv_bn(
                in_channels=in_channels,
                out_channels=out_channels,
                kernel_size=kernel_size,
                stride=stride,
                padding=padding,
                dilation=dilation,
                groups=groups,
            )

            self.dbb_avg = nn.Sequential()
            if groups < out_channels:
                self.dbb_avg.add_sublayer(
                    "conv",
                    nn.Conv2d(
                        in_channels=in_channels,
                        out_channels=out_channels,
                        kernel_size=1,
                        stride=1,
                        padding=0,
                        groups=groups,
                        bias=False,
                    ),
                )
                self.dbb_avg.add_sublayer(
                    "bn", BNAndPad(pad_pixels=padding, num_features=out_channels)
                )
                self.dbb_avg.add_sublayer(
                    "avg",
                    nn.AvgPool2D(kernel_size=kernel_size, stride=stride, padding=0),
                )
                self.dbb_1x1 = conv_bn(
                    in_channels=in_channels,
                    out_channels=out_channels,
                    kernel_size=1,
                    stride=stride,
                    padding=0,
                    groups=groups,
                )
            else:
                self.dbb_avg.add_sublayer(
                    "avg",
                    nn.AvgPool2D(
                        kernel_size=kernel_size, stride=stride, padding=padding
                    ),
                )

            self.dbb_avg.add_sublayer("avgbn", nn.BatchNorm2D(out_channels))

            if internal_channels_1x1_3x3 is None:
                internal_channels_1x1_3x3 = (
                    in_channels if groups < out_channels else 2 * in_channels
                )  # For mobilenet, it is better to have 2X internal channels

            self.dbb_1x1_kxk = nn.Sequential()
            if internal_channels_1x1_3x3 == in_channels:
                self.dbb_1x1_kxk.add_sublayer(
                    "idconv1", IdentityBasedConv1x1(channels=in_channels, groups=groups)
                )
            else:
                self.dbb_1x1_kxk.add_sublayer(
                    "conv1",
                    nn.Conv2d(
                        in_channels=in_channels,
                        out_channels=internal_channels_1x1_3x3,
                        kernel_size=1,
                        stride=1,
                        padding=0,
                        groups=groups,
                        bias=False,
                    ),
                )
            self.dbb_1x1_kxk.add_sublayer(
                "bn1",
                BNAndPad(pad_pixels=padding, num_features=internal_channels_1x1_3x3),
            )
            self.dbb_1x1_kxk.add_sublayer(
                "conv2",
                nn.Conv2d(
                    in_channels=internal_channels_1x1_3x3,
                    out_channels=out_channels,
                    kernel_size=kernel_size,
                    stride=stride,
                    padding=0,
                    groups=groups,
                    bias=False,
                ),
            )
            self.dbb_1x1_kxk.add_sublayer("bn2", nn.BatchNorm2D(out_channels))

        #   The experiments reported in the paper used the default initialization of bn.weight (all as 1). But changing the initialization may be useful in some cases.
        if single_init:
            #   Initialize the bn.weight of dbb_origin as 1 and others as 0. This is not the default setting.
            self.single_init()