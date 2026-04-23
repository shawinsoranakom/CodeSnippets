def __init__(
        self,
        ch_in,
        ch_out,
        filter_size,
        stride,
        groups=1,
        norm_type="bn",
        norm_decay=0.0,
        norm_groups=32,
        lr_scale=1.0,
        freeze_norm=False,
        initializer=Normal(mean=0.0, std=0.01),
    ):
        super(ConvNormLayer, self).__init__()
        assert norm_type in ["bn", "sync_bn", "gn"]

        bias_attr = False

        self.conv = nn.Conv2D(
            in_channels=ch_in,
            out_channels=ch_out,
            kernel_size=filter_size,
            stride=stride,
            padding=(filter_size - 1) // 2,
            groups=groups,
            weight_attr=ParamAttr(initializer=initializer, learning_rate=1.0),
            bias_attr=bias_attr,
        )

        norm_lr = 0.0 if freeze_norm else 1.0
        param_attr = ParamAttr(
            learning_rate=norm_lr,
            regularizer=L2Decay(norm_decay) if norm_decay is not None else None,
        )
        bias_attr = ParamAttr(
            learning_rate=norm_lr,
            regularizer=L2Decay(norm_decay) if norm_decay is not None else None,
        )
        if norm_type == "bn":
            self.norm = nn.BatchNorm2D(
                ch_out, weight_attr=param_attr, bias_attr=bias_attr
            )
        elif norm_type == "sync_bn":
            self.norm = nn.SyncBatchNorm(
                ch_out, weight_attr=param_attr, bias_attr=bias_attr
            )
        elif norm_type == "gn":
            self.norm = nn.GroupNorm(
                num_groups=norm_groups,
                num_channels=ch_out,
                weight_attr=param_attr,
                bias_attr=bias_attr,
            )