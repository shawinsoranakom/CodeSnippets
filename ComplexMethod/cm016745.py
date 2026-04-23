def __init__(self, levels=2, bottleneck_blocks=12, c_hidden=384, c_latent=4, codebook_size=8192):
        super().__init__()
        self.c_latent = c_latent
        c_levels = [c_hidden // (2 ** i) for i in reversed(range(levels))]

        # Encoder blocks
        self.in_block = nn.Sequential(
            nn.PixelUnshuffle(2),
            ops.Conv2d(3 * 4, c_levels[0], kernel_size=1)
        )
        down_blocks = []
        for i in range(levels):
            if i > 0:
                down_blocks.append(ops.Conv2d(c_levels[i - 1], c_levels[i], kernel_size=4, stride=2, padding=1))
            block = ResBlock(c_levels[i], c_levels[i] * 4)
            down_blocks.append(block)
        down_blocks.append(nn.Sequential(
            ops.Conv2d(c_levels[-1], c_latent, kernel_size=1, bias=False),
            nn.BatchNorm2d(c_latent),  # then normalize them to have mean 0 and std 1
        ))
        self.down_blocks = nn.Sequential(*down_blocks)
        self.down_blocks[0]

        self.codebook_size = codebook_size
        self.vquantizer = VectorQuantize(c_latent, k=codebook_size)

        # Decoder blocks
        up_blocks = [nn.Sequential(
            ops.Conv2d(c_latent, c_levels[-1], kernel_size=1)
        )]
        for i in range(levels):
            for j in range(bottleneck_blocks if i == 0 else 1):
                block = ResBlock(c_levels[levels - 1 - i], c_levels[levels - 1 - i] * 4)
                up_blocks.append(block)
            if i < levels - 1:
                up_blocks.append(
                    ops.ConvTranspose2d(c_levels[levels - 1 - i], c_levels[levels - 2 - i], kernel_size=4, stride=2,
                                       padding=1))
        self.up_blocks = nn.Sequential(*up_blocks)
        self.out_block = nn.Sequential(
            ops.Conv2d(c_levels[0], 3 * 4, kernel_size=1),
            nn.PixelShuffle(2),
        )