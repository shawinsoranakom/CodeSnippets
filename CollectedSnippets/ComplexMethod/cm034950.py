def __init__(
        self,
        in_channels,
        out_channels,
        stride,
        dw_size=3,
        split_pw=False,
        use_rep=False,
        use_se=False,
        use_shortcut=False,
    ):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.is_repped = False

        self.dw_size = dw_size
        self.split_pw = split_pw
        self.use_rep = use_rep
        self.use_se = use_se
        self.use_shortcut = (
            True
            if use_shortcut and stride == 1 and in_channels == out_channels
            else False
        )

        if self.use_rep:
            self.dw_conv_list = nn.LayerList()
            for kernel_size in range(self.dw_size, 0, -2):
                if kernel_size == 1 and stride != 1:
                    continue
                dw_conv = ConvBNLayer(
                    in_channels=in_channels,
                    out_channels=in_channels,
                    kernel_size=kernel_size,
                    stride=stride,
                    groups=in_channels,
                    use_act=False,
                )
                self.dw_conv_list.append(dw_conv)
            self.dw_conv = nn.Conv2D(
                in_channels=in_channels,
                out_channels=in_channels,
                kernel_size=dw_size,
                stride=stride,
                padding=(dw_size - 1) // 2,
                groups=in_channels,
            )
        else:
            self.dw_conv = ConvBNLayer(
                in_channels=in_channels,
                out_channels=in_channels,
                kernel_size=dw_size,
                stride=stride,
                groups=in_channels,
            )

        self.act = nn.ReLU()

        if use_se:
            self.se = SEModule(in_channels)

        if self.split_pw:
            pw_ratio = 0.5
            self.pw_conv_1 = ConvBNLayer(
                in_channels=in_channels,
                kernel_size=1,
                out_channels=int(out_channels * pw_ratio),
                stride=1,
            )
            self.pw_conv_2 = ConvBNLayer(
                in_channels=int(out_channels * pw_ratio),
                kernel_size=1,
                out_channels=out_channels,
                stride=1,
            )
        else:
            self.pw_conv = ConvBNLayer(
                in_channels=in_channels,
                kernel_size=1,
                out_channels=out_channels,
                stride=1,
            )