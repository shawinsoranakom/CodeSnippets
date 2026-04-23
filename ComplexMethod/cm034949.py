def __init__(
        self,
        scale=1.0,
        conv_kxk_num=4,
        lr_mult_list=[1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
        lab_lr=0.1,
        det=False,
        **kwargs,
    ):
        super().__init__()
        self.scale = scale
        self.lr_mult_list = lr_mult_list
        self.det = det

        self.net_config = NET_CONFIG_det if self.det else NET_CONFIG_rec

        assert isinstance(
            self.lr_mult_list, (list, tuple)
        ), "lr_mult_list should be in (list, tuple) but got {}".format(
            type(self.lr_mult_list)
        )
        assert (
            len(self.lr_mult_list) == 6
        ), "lr_mult_list length should be 6 but got {}".format(len(self.lr_mult_list))

        self.conv1 = ConvBNLayer(
            in_channels=3,
            out_channels=make_divisible(16 * scale),
            kernel_size=3,
            stride=2,
            lr_mult=self.lr_mult_list[0],
        )

        self.blocks2 = nn.Sequential(
            *[
                LCNetV3Block(
                    in_channels=make_divisible(in_c * scale),
                    out_channels=make_divisible(out_c * scale),
                    dw_size=k,
                    stride=s,
                    use_se=se,
                    conv_kxk_num=conv_kxk_num,
                    lr_mult=self.lr_mult_list[1],
                    lab_lr=lab_lr,
                )
                for i, (k, in_c, out_c, s, se) in enumerate(self.net_config["blocks2"])
            ]
        )

        self.blocks3 = nn.Sequential(
            *[
                LCNetV3Block(
                    in_channels=make_divisible(in_c * scale),
                    out_channels=make_divisible(out_c * scale),
                    dw_size=k,
                    stride=s,
                    use_se=se,
                    conv_kxk_num=conv_kxk_num,
                    lr_mult=self.lr_mult_list[2],
                    lab_lr=lab_lr,
                )
                for i, (k, in_c, out_c, s, se) in enumerate(self.net_config["blocks3"])
            ]
        )

        self.blocks4 = nn.Sequential(
            *[
                LCNetV3Block(
                    in_channels=make_divisible(in_c * scale),
                    out_channels=make_divisible(out_c * scale),
                    dw_size=k,
                    stride=s,
                    use_se=se,
                    conv_kxk_num=conv_kxk_num,
                    lr_mult=self.lr_mult_list[3],
                    lab_lr=lab_lr,
                )
                for i, (k, in_c, out_c, s, se) in enumerate(self.net_config["blocks4"])
            ]
        )

        self.blocks5 = nn.Sequential(
            *[
                LCNetV3Block(
                    in_channels=make_divisible(in_c * scale),
                    out_channels=make_divisible(out_c * scale),
                    dw_size=k,
                    stride=s,
                    use_se=se,
                    conv_kxk_num=conv_kxk_num,
                    lr_mult=self.lr_mult_list[4],
                    lab_lr=lab_lr,
                )
                for i, (k, in_c, out_c, s, se) in enumerate(self.net_config["blocks5"])
            ]
        )

        self.blocks6 = nn.Sequential(
            *[
                LCNetV3Block(
                    in_channels=make_divisible(in_c * scale),
                    out_channels=make_divisible(out_c * scale),
                    dw_size=k,
                    stride=s,
                    use_se=se,
                    conv_kxk_num=conv_kxk_num,
                    lr_mult=self.lr_mult_list[5],
                    lab_lr=lab_lr,
                )
                for i, (k, in_c, out_c, s, se) in enumerate(self.net_config["blocks6"])
            ]
        )
        self.out_channels = make_divisible(512 * scale)

        if self.det:
            mv_c = [16, 24, 56, 480]
            self.out_channels = [
                make_divisible(self.net_config["blocks3"][-1][2] * scale),
                make_divisible(self.net_config["blocks4"][-1][2] * scale),
                make_divisible(self.net_config["blocks5"][-1][2] * scale),
                make_divisible(self.net_config["blocks6"][-1][2] * scale),
            ]

            self.layer_list = nn.LayerList(
                [
                    nn.Conv2D(self.out_channels[0], int(mv_c[0] * scale), 1, 1, 0),
                    nn.Conv2D(self.out_channels[1], int(mv_c[1] * scale), 1, 1, 0),
                    nn.Conv2D(self.out_channels[2], int(mv_c[2] * scale), 1, 1, 0),
                    nn.Conv2D(self.out_channels[3], int(mv_c[3] * scale), 1, 1, 0),
                ]
            )
            self.out_channels = [
                int(mv_c[0] * scale),
                int(mv_c[1] * scale),
                int(mv_c[2] * scale),
                int(mv_c[3] * scale),
            ]