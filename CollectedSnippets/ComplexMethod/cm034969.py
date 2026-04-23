def __init__(
        self,
        layers,
        channels=(256, 512, 1024, 2048),
        num_classes=1000,
        in_chans=3,
        global_pool="avg",
        output_stride=32,
        width_factor=1,
        stem_chs=64,
        stem_type="",
        avg_down=False,
        preact=True,
        act_layer=nn.ReLU,
        conv_layer=StdConv2d,
        norm_layer=partial(GroupNormAct, num_groups=32),
        drop_rate=0.0,
        drop_path_rate=0.0,
        zero_init_last=False,
        is_export=False,
    ):
        super().__init__()
        self.num_classes = num_classes
        self.drop_rate = drop_rate
        self.is_export = is_export
        wf = width_factor
        self.feature_info = []
        stem_chs = make_div(stem_chs * wf)
        self.stem = create_resnetv2_stem(
            in_chans,
            stem_chs,
            stem_type,
            preact,
            conv_layer=conv_layer,
            norm_layer=norm_layer,
            is_export=is_export,
        )
        stem_feat = (
            ("stem.conv3" if is_stem_deep(stem_type) else "stem.conv")
            if preact
            else "stem.norm"
        )
        self.feature_info.append(dict(num_chs=stem_chs, reduction=2, module=stem_feat))

        prev_chs = stem_chs
        curr_stride = 4
        dilation = 1
        block_dprs = [
            x.tolist()
            for x in paddle.linspace(0, drop_path_rate, sum(layers)).split(layers)
        ]
        block_fn = PreActBottleneck if preact else Bottleneck
        self.stages = nn.Sequential()
        for stage_idx, (d, c, bdpr) in enumerate(zip(layers, channels, block_dprs)):
            out_chs = make_div(c * wf)
            stride = 1 if stage_idx == 0 else 2
            if curr_stride >= output_stride:
                dilation *= stride
                stride = 1
            stage = ResNetStage(
                prev_chs,
                out_chs,
                stride=stride,
                dilation=dilation,
                depth=d,
                avg_down=avg_down,
                act_layer=act_layer,
                conv_layer=conv_layer,
                norm_layer=norm_layer,
                block_dpr=bdpr,
                block_fn=block_fn,
                is_export=is_export,
            )
            prev_chs = out_chs
            curr_stride *= stride
            self.feature_info += [
                dict(
                    num_chs=prev_chs,
                    reduction=curr_stride,
                    module=f"stages.{stage_idx}",
                )
            ]
            self.stages.add_sublayer(str(stage_idx), stage)

        self.num_features = prev_chs
        self.norm = norm_layer(self.num_features) if preact else nn.Identity()
        self.head = ClassifierHead(
            self.num_features,
            num_classes,
            pool_type=global_pool,
            drop_rate=self.drop_rate,
            use_conv=True,
        )

        self.init_weights(zero_init_last=zero_init_last)