def __init__(
        self, in_channels=3, layers=50, dcn_stage=None, out_indices=None, **kwargs
    ):
        super(ResNet_vd, self).__init__()

        self.layers = layers
        supported_layers = [18, 34, 50, 101, 152, 200]
        assert (
            layers in supported_layers
        ), "supported layers are {} but input layer is {}".format(
            supported_layers, layers
        )

        if layers == 18:
            depth = [2, 2, 2, 2]
        elif layers == 34 or layers == 50:
            depth = [3, 4, 6, 3]
        elif layers == 101:
            depth = [3, 4, 23, 3]
        elif layers == 152:
            depth = [3, 8, 36, 3]
        elif layers == 200:
            depth = [3, 12, 48, 3]
        num_channels = [64, 256, 512, 1024] if layers >= 50 else [64, 64, 128, 256]
        num_filters = [64, 128, 256, 512]

        self.dcn_stage = (
            dcn_stage if dcn_stage is not None else [False, False, False, False]
        )
        self.out_indices = out_indices if out_indices is not None else [0, 1, 2, 3]

        self.conv1_1 = ConvBNLayer(
            in_channels=in_channels,
            out_channels=32,
            kernel_size=3,
            stride=2,
            act="relu",
        )
        self.conv1_2 = ConvBNLayer(
            in_channels=32, out_channels=32, kernel_size=3, stride=1, act="relu"
        )
        self.conv1_3 = ConvBNLayer(
            in_channels=32, out_channels=64, kernel_size=3, stride=1, act="relu"
        )
        self.pool2d_max = nn.MaxPool2D(kernel_size=3, stride=2, padding=1)

        self.stages = []
        self.out_channels = []
        if layers >= 50:
            for block in range(len(depth)):
                block_list = []
                shortcut = False
                is_dcn = self.dcn_stage[block]
                for i in range(depth[block]):
                    bottleneck_block = self.add_sublayer(
                        "bb_%d_%d" % (block, i),
                        BottleneckBlock(
                            in_channels=(
                                num_channels[block]
                                if i == 0
                                else num_filters[block] * 4
                            ),
                            out_channels=num_filters[block],
                            stride=2 if i == 0 and block != 0 else 1,
                            shortcut=shortcut,
                            if_first=block == i == 0,
                            is_dcn=is_dcn,
                        ),
                    )
                    shortcut = True
                    block_list.append(bottleneck_block)
                if block in self.out_indices:
                    self.out_channels.append(num_filters[block] * 4)
                self.stages.append(nn.Sequential(*block_list))
        else:
            for block in range(len(depth)):
                block_list = []
                shortcut = False
                for i in range(depth[block]):
                    basic_block = self.add_sublayer(
                        "bb_%d_%d" % (block, i),
                        BasicBlock(
                            in_channels=(
                                num_channels[block] if i == 0 else num_filters[block]
                            ),
                            out_channels=num_filters[block],
                            stride=2 if i == 0 and block != 0 else 1,
                            shortcut=shortcut,
                            if_first=block == i == 0,
                        ),
                    )
                    shortcut = True
                    block_list.append(basic_block)
                if block in self.out_indices:
                    self.out_channels.append(num_filters[block])
                self.stages.append(nn.Sequential(*block_list))