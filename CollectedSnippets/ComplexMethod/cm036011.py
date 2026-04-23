def __init__(self, n_blocks: List[int], n_channels: List[int],
                 bottlenecks: Optional[List[int]] = None,
                 img_channels: int = 3, first_kernel_size: int = 7):
        """
        * `n_blocks` is a list of of number of blocks for each feature map size.
        * `n_channels` is the number of channels for each feature map size.
        * `bottlenecks` is the number of channels the bottlenecks.
        If this is `None`, [residual blocks](#residual_block) are used.
        * `img_channels` is the number of channels in the input.
        * `first_kernel_size` is the kernel size of the initial convolution layer
        """
        super().__init__()

        # Number of blocks and number of channels for each feature map size
        assert len(n_blocks) == len(n_channels)
        # If [bottleneck residual blocks](#bottleneck_residual_block) are used,
        # the number of channels in bottlenecks should be provided for each feature map size
        assert bottlenecks is None or len(bottlenecks) == len(n_channels)

        # Initial convolution layer maps from `img_channels` to number of channels in the first
        # residual block (`n_channels[0]`)
        self.conv = nn.Conv2d(img_channels, n_channels[0],
                              kernel_size=first_kernel_size, stride=2, padding=first_kernel_size // 2)
        # Batch norm after initial convolution
        self.bn = nn.BatchNorm2d(n_channels[0])

        # List of blocks
        blocks = []
        # Number of channels from previous layer (or block)
        prev_channels = n_channels[0]
        # Loop through each feature map size
        for i, channels in enumerate(n_channels):
            # The first block for the new feature map size, will have a stride length of $2$
            # except fro the very first block
            stride = 2 if len(blocks) == 0 else 1

            if bottlenecks is None:
                # [residual blocks](#residual_block) that maps from `prev_channels` to `channels`
                blocks.append(ResidualBlock(prev_channels, channels, stride=stride))
            else:
                # [bottleneck residual blocks](#bottleneck_residual_block)
                # that maps from `prev_channels` to `channels`
                blocks.append(BottleneckResidualBlock(prev_channels, bottlenecks[i], channels,
                                                      stride=stride))

            # Change the number of channels
            prev_channels = channels
            # Add rest of the blocks - no change in feature map size or channels
            for _ in range(n_blocks[i] - 1):
                if bottlenecks is None:
                    # [residual blocks](#residual_block)
                    blocks.append(ResidualBlock(channels, channels, stride=1))
                else:
                    # [bottleneck residual blocks](#bottleneck_residual_block)
                    blocks.append(BottleneckResidualBlock(channels, bottlenecks[i], channels, stride=1))

        # Stack the blocks
        self.blocks = nn.Sequential(*blocks)