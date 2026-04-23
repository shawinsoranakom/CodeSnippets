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
            depth = [3, 4, 6, 3]
        elif layers == 101:
            depth = [3, 4, 23, 3]
        elif layers == 152:
            depth = [3, 8, 36, 3]
        elif layers == 200:
            depth = [3, 12, 48, 3]
        num_channels = [64, 256, 512, 1024] if layers >= 50 else [64, 64, 128, 256]
        num_filters = [64, 128, 256, 512]

        self.conv1_1 = ConvBNLayer(
            in_channels=in_channels,
            out_channels=32,
            kernel_size=3,
            stride=1,
            act="relu",
            name="conv1_1",
        )
        self.conv1_2 = ConvBNLayer(
            in_channels=32,
            out_channels=32,
            kernel_size=3,
            stride=1,
            act="relu",
            name="conv1_2",
        )
        self.conv1_3 = ConvBNLayer(
            in_channels=32,
            out_channels=64,
            kernel_size=3,
            stride=1,
            act="relu",
            name="conv1_3",
        )
        self.pool2d_max = nn.MaxPool2D(kernel_size=3, stride=2, padding=1)

        self.block_list = []
        if layers >= 50:
            for block in range(len(depth)):
                shortcut = False
                for i in range(depth[block]):
                    if layers in [101, 152, 200] and block == 2:
                        if i == 0:
                            conv_name = "res" + str(block + 2) + "a"
                        else:
                            conv_name = "res" + str(block + 2) + "b" + str(i)
                    else:
                        conv_name = "res" + str(block + 2) + chr(97 + i)

                    if i == 0 and block != 0:
                        stride = (2, 1)
                    else:
                        stride = (1, 1)
                    bottleneck_block = self.add_sublayer(
                        "bb_%d_%d" % (block, i),
                        BottleneckBlock(
                            in_channels=(
                                num_channels[block]
                                if i == 0
                                else num_filters[block] * 4
                            ),
                            out_channels=num_filters[block],
                            stride=stride,
                            shortcut=shortcut,
                            if_first=block == i == 0,
                            name=conv_name,
                        ),
                    )
                    shortcut = True
                    self.block_list.append(bottleneck_block)
                self.out_channels = num_filters[block] * 4
        else:
            for block in range(len(depth)):
                shortcut = False
                for i in range(depth[block]):
                    conv_name = "res" + str(block + 2) + chr(97 + i)
                    if i == 0 and block != 0:
                        stride = (2, 1)
                    else:
                        stride = (1, 1)

                    basic_block = self.add_sublayer(
                        "bb_%d_%d" % (block, i),
                        BasicBlock(
                            in_channels=(
                                num_channels[block] if i == 0 else num_filters[block]
                            ),
                            out_channels=num_filters[block],
                            stride=stride,
                            shortcut=shortcut,
                            if_first=block == i == 0,
                            name=conv_name,
                        ),
                    )
                    shortcut = True
                    self.block_list.append(basic_block)
                self.out_channels = num_filters[block]
        self.out_pool = nn.MaxPool2D(kernel_size=2, stride=2, padding=0)