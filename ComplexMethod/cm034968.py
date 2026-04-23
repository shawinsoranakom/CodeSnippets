def __init__(
        self,
        in_chs,
        out_chs=None,
        bottle_ratio=0.25,
        stride=1,
        dilation=1,
        first_dilation=None,
        groups=1,
        act_layer=None,
        conv_layer=None,
        norm_layer=None,
        proj_layer=None,
        drop_path_rate=0.0,
        is_export=False,
    ):
        super().__init__()
        first_dilation = first_dilation or dilation
        act_layer = act_layer or nn.ReLU
        conv_layer = conv_layer or StdConv2d
        norm_layer = norm_layer or partial(GroupNormAct, num_groups=32)
        out_chs = out_chs or in_chs
        mid_chs = make_div(out_chs * bottle_ratio)

        if proj_layer is not None:
            self.downsample = proj_layer(
                in_chs,
                out_chs,
                stride=stride,
                dilation=dilation,
                preact=False,
                conv_layer=conv_layer,
                norm_layer=norm_layer,
                is_export=is_export,
            )
        else:
            self.downsample = None

        self.conv1 = conv_layer(in_chs, mid_chs, 1, is_export=is_export)
        self.norm1 = norm_layer(mid_chs)
        self.conv2 = conv_layer(
            mid_chs,
            mid_chs,
            3,
            stride=stride,
            dilation=first_dilation,
            groups=groups,
            is_export=is_export,
        )
        self.norm2 = norm_layer(mid_chs)
        self.conv3 = conv_layer(mid_chs, out_chs, 1, is_export=is_export)
        self.norm3 = norm_layer(out_chs, apply_act=False)
        self.drop_path = (
            DropPath(drop_path_rate) if drop_path_rate > 0 else nn.Identity()
        )
        self.act3 = act_layer()