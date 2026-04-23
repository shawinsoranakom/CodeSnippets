def _make_fuse_layers(self) -> nn.ModuleList | None:
        """Make the fuse layers for the HR Module

        Returns
        -------
        The fuse layers module list or ``None`` if layers are not to be fused
        """
        if self.num_branches == 1:
            return None

        num_branches = self.num_branches
        num_in_channels = self.num_in_channels
        fuse_layers = []
        for i in range(num_branches if self.multi_scale_output else 1):
            fuse_layer = []
            for j in range(num_branches):
                if j > i:
                    fuse_layer.append(nn.Sequential(nn.Conv2d(num_in_channels[j],
                                                              num_in_channels[i],
                                                              1,
                                                              stride=1,
                                                              padding=0,
                                                              bias=False),
                                                    nn.BatchNorm2d(num_in_channels[i],
                                                                   momentum=0.01)))
                elif j == i:
                    fuse_layer.append(None)  # type:ignore[arg-type]
                else:
                    conv3x3s = []
                    for k in range(i - j):
                        if k == i - j - 1:
                            num_out_channels_conv3x3 = num_in_channels[i]
                            conv3x3s.append(nn.Sequential(nn.Conv2d(num_in_channels[j],
                                                                    num_out_channels_conv3x3,
                                                                    3,
                                                                    stride=2,
                                                                    padding=1,
                                                                    bias=False),
                                                          nn.BatchNorm2d(num_out_channels_conv3x3,
                                                                         momentum=0.01)))
                        else:
                            num_out_channels_conv3x3 = num_in_channels[j]
                            conv3x3s.append(nn.Sequential(nn.Conv2d(num_in_channels[j],
                                                                    num_out_channels_conv3x3,
                                                                    3,
                                                                    stride=2,
                                                                    padding=1,
                                                                    bias=False),
                                                          nn.BatchNorm2d(num_out_channels_conv3x3,
                                                                         momentum=0.01),
                                                          nn.ReLU(inplace=True)))
                    fuse_layer.append(nn.Sequential(*conv3x3s))
            fuse_layers.append(nn.ModuleList(fuse_layer))

        return nn.ModuleList(fuse_layers)