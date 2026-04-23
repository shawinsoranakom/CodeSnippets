def __init__(
        self,
        in_channels: int,
        latent_channels: int,
        attention_head_dim: int = 32,
        block_type: str or tuple = "ResBlock",
        block_out_channels: tuple = (128, 256, 512, 512, 1024, 1024),
        layers_per_block: tuple = (2, 2, 2, 2, 2, 2),
        qkv_multiscales: tuple = ((), (), (), (5,), (5,), (5,)),
        downsample_block_type: str = "pixel_unshuffle",
        out_shortcut: bool = True,
    ):
        super().__init__()

        num_blocks = len(block_out_channels)

        if isinstance(block_type, str):
            block_type = (block_type,) * num_blocks

        if layers_per_block[0] > 0:
            self.conv_in = ops.Conv2d(
                in_channels,
                block_out_channels[0] if layers_per_block[0] > 0 else block_out_channels[1],
                kernel_size=3,
                stride=1,
                padding=1,
            )
        else:
            self.conv_in = DCDownBlock2d(
                in_channels=in_channels,
                out_channels=block_out_channels[0] if layers_per_block[0] > 0 else block_out_channels[1],
                downsample=downsample_block_type == "pixel_unshuffle",
                shortcut=False,
            )

        down_blocks = []
        for i, (out_channel, num_layers) in enumerate(zip(block_out_channels, layers_per_block)):
            down_block_list = []

            for _ in range(num_layers):
                block = get_block(
                    block_type[i],
                    out_channel,
                    out_channel,
                    attention_head_dim=attention_head_dim,
                    norm_type="rms_norm",
                    act_fn="silu",
                    qkv_mutliscales=qkv_multiscales[i],
                )
                down_block_list.append(block)

            if i < num_blocks - 1 and num_layers > 0:
                downsample_block = DCDownBlock2d(
                    in_channels=out_channel,
                    out_channels=block_out_channels[i + 1],
                    downsample=downsample_block_type == "pixel_unshuffle",
                    shortcut=True,
                )
                down_block_list.append(downsample_block)

            down_blocks.append(nn.Sequential(*down_block_list))

        self.down_blocks = nn.ModuleList(down_blocks)

        self.conv_out = ops.Conv2d(block_out_channels[-1], latent_channels, 3, 1, 1)

        self.out_shortcut = out_shortcut
        if out_shortcut:
            self.out_shortcut_average_group_size = block_out_channels[-1] // latent_channels