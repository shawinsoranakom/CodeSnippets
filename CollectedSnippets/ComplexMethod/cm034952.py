def __init__(
        self,
        inp,
        oup,
        kernel_size=3,
        stride=1,
        ch_exp=(2, 2),
        ch_per_group=4,
        groups_1x1=(1, 1),
        depthsep=True,
        shuffle=False,
        activation_cfg=None,
    ):
        super(DYMicroBlock, self).__init__()

        self.identity = stride == 1 and inp == oup

        y1, y2, y3 = activation_cfg["dy"]
        act_reduction = 8 * activation_cfg["ratio"]
        init_a = activation_cfg["init_a"]
        init_b = activation_cfg["init_b"]

        t1 = ch_exp
        gs1 = ch_per_group
        hidden_fft, g1, g2 = groups_1x1
        hidden_dim2 = inp * t1[0] * t1[1]

        if gs1[0] == 0:
            self.layers = nn.Sequential(
                DepthSpatialSepConv(inp, t1, kernel_size, stride),
                (
                    DYShiftMax(
                        hidden_dim2,
                        hidden_dim2,
                        act_max=2.0,
                        act_relu=True if y2 == 2 else False,
                        init_a=init_a,
                        reduction=act_reduction,
                        init_b=init_b,
                        g=gs1,
                        expansion=False,
                    )
                    if y2 > 0
                    else nn.ReLU6()
                ),
                ChannelShuffle(gs1[1]) if shuffle else nn.Sequential(),
                (
                    ChannelShuffle(hidden_dim2 // 2)
                    if shuffle and y2 != 0
                    else nn.Sequential()
                ),
                GroupConv(hidden_dim2, oup, (g1, g2)),
                (
                    DYShiftMax(
                        oup,
                        oup,
                        act_max=2.0,
                        act_relu=False,
                        init_a=[1.0, 0.0],
                        reduction=act_reduction // 2,
                        init_b=[0.0, 0.0],
                        g=(g1, g2),
                        expansion=False,
                    )
                    if y3 > 0
                    else nn.Sequential()
                ),
                ChannelShuffle(g2) if shuffle else nn.Sequential(),
                (
                    ChannelShuffle(oup // 2)
                    if shuffle and oup % 2 == 0 and y3 != 0
                    else nn.Sequential()
                ),
            )
        elif g2 == 0:
            self.layers = nn.Sequential(
                GroupConv(inp, hidden_dim2, gs1),
                (
                    DYShiftMax(
                        hidden_dim2,
                        hidden_dim2,
                        act_max=2.0,
                        act_relu=False,
                        init_a=[1.0, 0.0],
                        reduction=act_reduction,
                        init_b=[0.0, 0.0],
                        g=gs1,
                        expansion=False,
                    )
                    if y3 > 0
                    else nn.Sequential()
                ),
            )
        else:
            self.layers = nn.Sequential(
                GroupConv(inp, hidden_dim2, gs1),
                (
                    DYShiftMax(
                        hidden_dim2,
                        hidden_dim2,
                        act_max=2.0,
                        act_relu=True if y1 == 2 else False,
                        init_a=init_a,
                        reduction=act_reduction,
                        init_b=init_b,
                        g=gs1,
                        expansion=False,
                    )
                    if y1 > 0
                    else nn.ReLU6()
                ),
                ChannelShuffle(gs1[1]) if shuffle else nn.Sequential(),
                (
                    DepthSpatialSepConv(hidden_dim2, (1, 1), kernel_size, stride)
                    if depthsep
                    else DepthConv(hidden_dim2, hidden_dim2, kernel_size, stride)
                ),
                nn.Sequential(),
                (
                    DYShiftMax(
                        hidden_dim2,
                        hidden_dim2,
                        act_max=2.0,
                        act_relu=True if y2 == 2 else False,
                        init_a=init_a,
                        reduction=act_reduction,
                        init_b=init_b,
                        g=gs1,
                        expansion=True,
                    )
                    if y2 > 0
                    else nn.ReLU6()
                ),
                (
                    ChannelShuffle(hidden_dim2 // 4)
                    if shuffle and y1 != 0 and y2 != 0
                    else (
                        nn.Sequential()
                        if y1 == 0 and y2 == 0
                        else ChannelShuffle(hidden_dim2 // 2)
                    )
                ),
                GroupConv(hidden_dim2, oup, (g1, g2)),
                (
                    DYShiftMax(
                        oup,
                        oup,
                        act_max=2.0,
                        act_relu=False,
                        init_a=[1.0, 0.0],
                        reduction=(
                            act_reduction // 2 if oup < hidden_dim2 else act_reduction
                        ),
                        init_b=[0.0, 0.0],
                        g=(g1, g2),
                        expansion=False,
                    )
                    if y3 > 0
                    else nn.Sequential()
                ),
                ChannelShuffle(g2) if shuffle else nn.Sequential(),
                ChannelShuffle(oup // 2) if shuffle and y3 != 0 else nn.Sequential(),
            )