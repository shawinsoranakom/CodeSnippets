def __init__(self, in_channels=1, layers=50, **kwargs):
        super(ResNetFPN, self).__init__()
        supported_layers = {
            18: {"depth": [2, 2, 2, 2], "block_class": BasicBlock},
            34: {"depth": [3, 4, 6, 3], "block_class": BasicBlock},
            50: {"depth": [3, 4, 6, 3], "block_class": BottleneckBlock},
            101: {"depth": [3, 4, 23, 3], "block_class": BottleneckBlock},
            152: {"depth": [3, 8, 36, 3], "block_class": BottleneckBlock},
        }
        stride_list = [(2, 2), (2, 2), (1, 1), (1, 1)]
        num_filters = [64, 128, 256, 512]
        self.depth = supported_layers[layers]["depth"]
        self.F = []
        self.conv = ConvBNLayer(
            in_channels=in_channels,
            out_channels=64,
            kernel_size=7,
            stride=2,
            act="relu",
            name="conv1",
        )
        self.block_list = []
        in_ch = 64
        if layers >= 50:
            for block in range(len(self.depth)):
                for i in range(self.depth[block]):
                    if layers in [101, 152] and block == 2:
                        if i == 0:
                            conv_name = "res" + str(block + 2) + "a"
                        else:
                            conv_name = "res" + str(block + 2) + "b" + str(i)
                    else:
                        conv_name = "res" + str(block + 2) + chr(97 + i)
                    block_list = self.add_sublayer(
                        "bottleneckBlock_{}_{}".format(block, i),
                        BottleneckBlock(
                            in_channels=in_ch,
                            out_channels=num_filters[block],
                            stride=stride_list[block] if i == 0 else 1,
                            name=conv_name,
                        ),
                    )
                    in_ch = num_filters[block] * 4
                    self.block_list.append(block_list)
                self.F.append(block_list)
        else:
            for block in range(len(self.depth)):
                for i in range(self.depth[block]):
                    conv_name = "res" + str(block + 2) + chr(97 + i)
                    if i == 0 and block != 0:
                        stride = (2, 1)
                    else:
                        stride = (1, 1)
                    basic_block = self.add_sublayer(
                        conv_name,
                        BasicBlock(
                            in_channels=in_ch,
                            out_channels=num_filters[block],
                            stride=stride_list[block] if i == 0 else 1,
                            is_first=block == i == 0,
                            name=conv_name,
                        ),
                    )
                    in_ch = basic_block.out_channels
                    self.block_list.append(basic_block)
        out_ch_list = [in_ch // 4, in_ch // 2, in_ch]
        self.base_block = []
        self.conv_trans = []
        self.bn_block = []
        for i in [-2, -3]:
            in_channels = out_ch_list[i + 1] + out_ch_list[i]

            self.base_block.append(
                self.add_sublayer(
                    "F_{}_base_block_0".format(i),
                    nn.Conv2D(
                        in_channels=in_channels,
                        out_channels=out_ch_list[i],
                        kernel_size=1,
                        weight_attr=ParamAttr(trainable=True),
                        bias_attr=ParamAttr(trainable=True),
                    ),
                )
            )
            self.base_block.append(
                self.add_sublayer(
                    "F_{}_base_block_1".format(i),
                    nn.Conv2D(
                        in_channels=out_ch_list[i],
                        out_channels=out_ch_list[i],
                        kernel_size=3,
                        padding=1,
                        weight_attr=ParamAttr(trainable=True),
                        bias_attr=ParamAttr(trainable=True),
                    ),
                )
            )
            self.base_block.append(
                self.add_sublayer(
                    "F_{}_base_block_2".format(i),
                    nn.BatchNorm(
                        num_channels=out_ch_list[i],
                        act="relu",
                        param_attr=ParamAttr(trainable=True),
                        bias_attr=ParamAttr(trainable=True),
                    ),
                )
            )
        self.base_block.append(
            self.add_sublayer(
                "F_{}_base_block_3".format(i),
                nn.Conv2D(
                    in_channels=out_ch_list[i],
                    out_channels=512,
                    kernel_size=1,
                    bias_attr=ParamAttr(trainable=True),
                    weight_attr=ParamAttr(trainable=True),
                ),
            )
        )
        self.out_channels = 512