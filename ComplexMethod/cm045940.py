def __init__(
        self,
        stem_channels,
        stage_config,
        layer_num,
        in_channels=3,
        det=False,
        out_indices=None,
    ):
        super().__init__()
        self.det = det
        self.out_indices = out_indices if out_indices is not None else [0, 1, 2, 3]

        # stem
        stem_channels.insert(0, in_channels)
        self.stem = nn.Sequential(
            *[
                ConvBNAct(
                    in_channels=stem_channels[i],
                    out_channels=stem_channels[i + 1],
                    kernel_size=3,
                    stride=2 if i == 0 else 1,
                )
                for i in range(len(stem_channels) - 1)
            ]
        )

        if self.det:
            self.pool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        # stages
        self.stages = nn.ModuleList()
        self.out_channels = []
        for block_id, k in enumerate(stage_config):
            (
                in_channels,
                mid_channels,
                out_channels,
                block_num,
                downsample,
                stride,
            ) = stage_config[k]
            self.stages.append(
                HG_Stage(
                    in_channels,
                    mid_channels,
                    out_channels,
                    block_num,
                    layer_num,
                    downsample,
                    stride,
                )
            )
            if block_id in self.out_indices:
                self.out_channels.append(out_channels)

        if not self.det:
            self.out_channels = stage_config["stage4"][2]

        self._init_weights()