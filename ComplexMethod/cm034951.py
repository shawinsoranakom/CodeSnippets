def __init__(self, in_channels=3, layers=50, **kwargs):
        super(ResNet, self).__init__()

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
            # depth = [3, 4, 6, 3]
            depth = [3, 4, 6, 3, 3]
        elif layers == 101:
            depth = [3, 4, 23, 3]
        elif layers == 152:
            depth = [3, 8, 36, 3]
        elif layers == 200:
            depth = [3, 12, 48, 3]
        num_channels = (
            [64, 256, 512, 1024, 2048] if layers >= 50 else [64, 64, 128, 256]
        )
        num_filters = [64, 128, 256, 512, 512]

        self.conv1_1 = ConvBNLayer(
            in_channels=in_channels,
            out_channels=64,
            kernel_size=7,
            stride=2,
            act="relu",
            name="conv1_1",
        )
        self.pool2d_max = nn.MaxPool2D(kernel_size=3, stride=2, padding=1)

        self.stages = []
        self.out_channels = [3, 64]
        # num_filters = [64, 128, 256, 512, 512]
        if layers >= 50:
            for block in range(len(depth)):
                block_list = []
                shortcut = False
                for i in range(depth[block]):
                    if layers in [101, 152] and block == 2:
                        if i == 0:
                            conv_name = "res" + str(block + 2) + "a"
                        else:
                            conv_name = "res" + str(block + 2) + "b" + str(i)
                    else:
                        conv_name = "res" + str(block + 2) + chr(97 + i)
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
                            name=conv_name,
                        ),
                    )
                    shortcut = True
                    block_list.append(bottleneck_block)
                self.out_channels.append(num_filters[block] * 4)
                self.stages.append(nn.Sequential(*block_list))
        else:
            for block in range(len(depth)):
                block_list = []
                shortcut = False
                for i in range(depth[block]):
                    conv_name = "res" + str(block + 2) + chr(97 + i)
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
                            name=conv_name,
                        ),
                    )
                    shortcut = True
                    block_list.append(basic_block)
                self.out_channels.append(num_filters[block])
                self.stages.append(nn.Sequential(*block_list))