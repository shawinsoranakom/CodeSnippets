def __init__(self, in_channels=3, layers=50, out_indices=None, dcn_stage=None):
        super(ResNet, self).__init__()

        self.layers = layers
        self.input_image_channel = in_channels

        supported_layers = [18, 34, 50, 101, 152]
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
        num_channels = [64, 256, 512, 1024] if layers >= 50 else [64, 64, 128, 256]
        num_filters = [64, 128, 256, 512]

        self.dcn_stage = (
            dcn_stage if dcn_stage is not None else [False, False, False, False]
        )
        self.out_indices = out_indices if out_indices is not None else [0, 1, 2, 3]

        self.conv = ConvBNLayer(
            in_channels=self.input_image_channel,
            out_channels=64,
            kernel_size=7,
            stride=2,
            act="relu",
        )
        self.pool2d_max = MaxPool2D(
            kernel_size=3,
            stride=2,
            padding=1,
        )

        self.stages = []
        self.out_channels = []
        if layers >= 50:
            for block in range(len(depth)):
                shortcut = False
                block_list = []
                is_dcn = self.dcn_stage[block]
                for i in range(depth[block]):
                    if layers in [101, 152] and block == 2:
                        if i == 0:
                            conv_name = "res" + str(block + 2) + "a"
                        else:
                            conv_name = "res" + str(block + 2) + "b" + str(i)
                    else:
                        conv_name = "res" + str(block + 2) + chr(97 + i)
                    bottleneck_block = self.add_sublayer(
                        conv_name,
                        BottleneckBlock(
                            num_channels=(
                                num_channels[block]
                                if i == 0
                                else num_filters[block] * 4
                            ),
                            num_filters=num_filters[block],
                            stride=2 if i == 0 and block != 0 else 1,
                            shortcut=shortcut,
                            is_dcn=is_dcn,
                        ),
                    )
                    block_list.append(bottleneck_block)
                    shortcut = True
                if block in self.out_indices:
                    self.out_channels.append(num_filters[block] * 4)
                self.stages.append(nn.Sequential(*block_list))
        else:
            for block in range(len(depth)):
                shortcut = False
                block_list = []
                for i in range(depth[block]):
                    conv_name = "res" + str(block + 2) + chr(97 + i)
                    basic_block = self.add_sublayer(
                        conv_name,
                        BasicBlock(
                            num_channels=(
                                num_channels[block] if i == 0 else num_filters[block]
                            ),
                            num_filters=num_filters[block],
                            stride=2 if i == 0 and block != 0 else 1,
                            shortcut=shortcut,
                        ),
                    )
                    block_list.append(basic_block)
                    shortcut = True
                if block in self.out_indices:
                    self.out_channels.append(num_filters[block])
                self.stages.append(nn.Sequential(*block_list))