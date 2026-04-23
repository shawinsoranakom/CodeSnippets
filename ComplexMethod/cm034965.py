def __init__(
        self,
        stage_config,
        stem_channels=[3, 32, 64],
        use_lab=False,
        use_last_conv=True,
        class_expand=2048,
        dropout_prob=0.0,
        class_num=1000,
        lr_mult_list=[1.0, 1.0, 1.0, 1.0, 1.0],
        det=False,
        text_rec=False,
        out_indices=None,
        **kwargs,
    ):
        super().__init__()
        self.det = det
        self.text_rec = text_rec
        self.use_lab = use_lab
        self.use_last_conv = use_last_conv
        self.class_expand = class_expand
        self.class_num = class_num
        self.out_indices = out_indices if out_indices is not None else [0, 1, 2, 3]
        self.out_channels = []

        # stem
        self.stem = StemBlock(
            in_channels=stem_channels[0],
            mid_channels=stem_channels[1],
            out_channels=stem_channels[2],
            use_lab=use_lab,
            lr_mult=lr_mult_list[0],
            text_rec=text_rec,
        )

        # stages
        self.stages = nn.LayerList()
        for i, k in enumerate(stage_config):
            (
                in_channels,
                mid_channels,
                out_channels,
                block_num,
                is_downsample,
                light_block,
                kernel_size,
                layer_num,
                stride,
            ) = stage_config[k]
            self.stages.append(
                HGV2_Stage(
                    in_channels,
                    mid_channels,
                    out_channels,
                    block_num,
                    layer_num,
                    is_downsample,
                    light_block,
                    kernel_size,
                    use_lab,
                    stride,
                    lr_mult=lr_mult_list[i + 1],
                )
            )
            if i in self.out_indices:
                self.out_channels.append(out_channels)
        if not self.det:
            self.out_channels = stage_config["stage4"][2]

        self.avg_pool = AdaptiveAvgPool2D(1)

        if self.use_last_conv:
            self.last_conv = Conv2D(
                in_channels=out_channels,
                out_channels=self.class_expand,
                kernel_size=1,
                stride=1,
                padding=0,
                bias_attr=False,
            )
            self.act = ReLU()
            if self.use_lab:
                self.lab = LearnableAffineBlock()
            self.dropout = nn.Dropout(p=dropout_prob, mode="downscale_in_infer")

        self.flatten = nn.Flatten(start_axis=1, stop_axis=-1)
        if not self.det:
            self.fc = nn.Linear(
                self.class_expand if self.use_last_conv else out_channels,
                self.class_num,
            )

        self._init_weights()