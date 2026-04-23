def __init__(
        self,
        in_channels,
        out_channels,
        spatial_scales=[0.25, 0.125, 0.0625, 0.03125],
        has_extra_convs=False,
        extra_stage=1,
        use_c5=True,
        norm_type=None,
        norm_decay=0.0,
        freeze_norm=False,
        relu_before_extra_convs=True,
    ):
        super(FCEFPN, self).__init__()
        self.out_channels = out_channels
        for s in range(extra_stage):
            spatial_scales = spatial_scales + [spatial_scales[-1] / 2.0]
        self.spatial_scales = spatial_scales
        self.has_extra_convs = has_extra_convs
        self.extra_stage = extra_stage
        self.use_c5 = use_c5
        self.relu_before_extra_convs = relu_before_extra_convs
        self.norm_type = norm_type
        self.norm_decay = norm_decay
        self.freeze_norm = freeze_norm

        self.lateral_convs = []
        self.fpn_convs = []
        fan = out_channels * 3 * 3

        # stage index 0,1,2,3 stands for res2,res3,res4,res5 on ResNet Backbone
        # 0 <= st_stage < ed_stage <= 3
        st_stage = 4 - len(in_channels)
        ed_stage = st_stage + len(in_channels) - 1
        for i in range(st_stage, ed_stage + 1):
            if i == 3:
                lateral_name = "fpn_inner_res5_sum"
            else:
                lateral_name = "fpn_inner_res{}_sum_lateral".format(i + 2)
            in_c = in_channels[i - st_stage]
            if self.norm_type is not None:
                lateral = self.add_sublayer(
                    lateral_name,
                    ConvNormLayer(
                        ch_in=in_c,
                        ch_out=out_channels,
                        filter_size=1,
                        stride=1,
                        norm_type=self.norm_type,
                        norm_decay=self.norm_decay,
                        freeze_norm=self.freeze_norm,
                        initializer=XavierUniform(fan_out=in_c),
                    ),
                )
            else:
                lateral = self.add_sublayer(
                    lateral_name,
                    nn.Conv2D(
                        in_channels=in_c,
                        out_channels=out_channels,
                        kernel_size=1,
                        weight_attr=ParamAttr(initializer=XavierUniform(fan_out=in_c)),
                    ),
                )
            self.lateral_convs.append(lateral)

        for i in range(st_stage, ed_stage + 1):
            fpn_name = "fpn_res{}_sum".format(i + 2)
            if self.norm_type is not None:
                fpn_conv = self.add_sublayer(
                    fpn_name,
                    ConvNormLayer(
                        ch_in=out_channels,
                        ch_out=out_channels,
                        filter_size=3,
                        stride=1,
                        norm_type=self.norm_type,
                        norm_decay=self.norm_decay,
                        freeze_norm=self.freeze_norm,
                        initializer=XavierUniform(fan_out=fan),
                    ),
                )
            else:
                fpn_conv = self.add_sublayer(
                    fpn_name,
                    nn.Conv2D(
                        in_channels=out_channels,
                        out_channels=out_channels,
                        kernel_size=3,
                        padding=1,
                        weight_attr=ParamAttr(initializer=XavierUniform(fan_out=fan)),
                    ),
                )
            self.fpn_convs.append(fpn_conv)

        # add extra conv levels for RetinaNet(use_c5)/FCOS(use_p5)
        if self.has_extra_convs:
            for i in range(self.extra_stage):
                lvl = ed_stage + 1 + i
                if i == 0 and self.use_c5:
                    in_c = in_channels[-1]
                else:
                    in_c = out_channels
                extra_fpn_name = "fpn_{}".format(lvl + 2)
                if self.norm_type is not None:
                    extra_fpn_conv = self.add_sublayer(
                        extra_fpn_name,
                        ConvNormLayer(
                            ch_in=in_c,
                            ch_out=out_channels,
                            filter_size=3,
                            stride=2,
                            norm_type=self.norm_type,
                            norm_decay=self.norm_decay,
                            freeze_norm=self.freeze_norm,
                            initializer=XavierUniform(fan_out=fan),
                        ),
                    )
                else:
                    extra_fpn_conv = self.add_sublayer(
                        extra_fpn_name,
                        nn.Conv2D(
                            in_channels=in_c,
                            out_channels=out_channels,
                            kernel_size=3,
                            stride=2,
                            padding=1,
                            weight_attr=ParamAttr(
                                initializer=XavierUniform(fan_out=fan)
                            ),
                        ),
                    )
                self.fpn_convs.append(extra_fpn_conv)