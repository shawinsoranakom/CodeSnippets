def __init__(
        self, in_channels=3, model_name="large", scale=0.5, disable_se=False, **kwargs
    ):
        """
        the MobilenetV3 backbone network for detection module.
        Args:
            params(dict): the super parameters for build network
        """
        super(MobileNetV3, self).__init__()

        self.disable_se = disable_se

        if model_name == "large":
            cfg = [
                # k, exp, c,  se,     nl,  s,
                [3, 16, 16, False, "relu", 1],
                [3, 64, 24, False, "relu", 2],
                [3, 72, 24, False, "relu", 1],
                [5, 72, 40, True, "relu", 2],
                [5, 120, 40, True, "relu", 1],
                [5, 120, 40, True, "relu", 1],
                [3, 240, 80, False, "hardswish", 2],
                [3, 200, 80, False, "hardswish", 1],
                [3, 184, 80, False, "hardswish", 1],
                [3, 184, 80, False, "hardswish", 1],
                [3, 480, 112, True, "hardswish", 1],
                [3, 672, 112, True, "hardswish", 1],
                [5, 672, 160, True, "hardswish", 2],
                [5, 960, 160, True, "hardswish", 1],
                [5, 960, 160, True, "hardswish", 1],
            ]
            cls_ch_squeeze = 960
        elif model_name == "small":
            cfg = [
                # k, exp, c,  se,     nl,  s,
                [3, 16, 16, True, "relu", 2],
                [3, 72, 24, False, "relu", 2],
                [3, 88, 24, False, "relu", 1],
                [5, 96, 40, True, "hardswish", 2],
                [5, 240, 40, True, "hardswish", 1],
                [5, 240, 40, True, "hardswish", 1],
                [5, 120, 48, True, "hardswish", 1],
                [5, 144, 48, True, "hardswish", 1],
                [5, 288, 96, True, "hardswish", 2],
                [5, 576, 96, True, "hardswish", 1],
                [5, 576, 96, True, "hardswish", 1],
            ]
            cls_ch_squeeze = 576
        else:
            raise NotImplementedError(
                "mode[" + model_name + "_model] is not implemented!"
            )

        supported_scale = [0.35, 0.5, 0.75, 1.0, 1.25]
        assert (
            scale in supported_scale
        ), "supported scale are {} but input scale is {}".format(supported_scale, scale)
        inplanes = 16
        # conv1
        self.conv = ConvBNLayer(
            in_channels=in_channels,
            out_channels=make_divisible(inplanes * scale),
            kernel_size=3,
            stride=2,
            padding=1,
            groups=1,
            if_act=True,
            act="hardswish",
        )

        self.stages = []
        self.out_channels = []
        block_list = []
        i = 0
        inplanes = make_divisible(inplanes * scale)
        for k, exp, c, se, nl, s in cfg:
            se = se and not self.disable_se
            start_idx = 2 if model_name == "large" else 0
            if s == 2 and i > start_idx:
                self.out_channels.append(inplanes)
                self.stages.append(nn.Sequential(*block_list))
                block_list = []
            block_list.append(
                ResidualUnit(
                    in_channels=inplanes,
                    mid_channels=make_divisible(scale * exp),
                    out_channels=make_divisible(scale * c),
                    kernel_size=k,
                    stride=s,
                    use_se=se,
                    act=nl,
                )
            )
            inplanes = make_divisible(scale * c)
            i += 1
        block_list.append(
            ConvBNLayer(
                in_channels=inplanes,
                out_channels=make_divisible(scale * cls_ch_squeeze),
                kernel_size=1,
                stride=1,
                padding=0,
                groups=1,
                if_act=True,
                act="hardswish",
            )
        )
        self.stages.append(nn.Sequential(*block_list))
        self.out_channels.append(make_divisible(scale * cls_ch_squeeze))
        for i, stage in enumerate(self.stages):
            self.add_sublayer(sublayer=stage, name="stage{}".format(i))