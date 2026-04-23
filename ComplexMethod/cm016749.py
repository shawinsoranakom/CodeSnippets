def __init__(self, c_in=4, c_out=4, c_r=64, patch_size=2, c_cond=1280, c_hidden=[320, 640, 1280, 1280],
                 nhead=[-1, -1, 20, 20], blocks=[[2, 6, 28, 6], [6, 28, 6, 2]],
                 block_repeat=[[1, 1, 1, 1], [3, 3, 2, 2]], level_config=['CT', 'CT', 'CTA', 'CTA'], c_clip=1280,
                 c_clip_seq=4, c_effnet=16, c_pixels=3, kernel_size=3, dropout=[0, 0, 0.0, 0.0], self_attn=True,
                 t_conds=['sca'], stable_cascade_stage=None, dtype=None, device=None, operations=None):
        super().__init__()
        self.dtype = dtype
        self.c_r = c_r
        self.t_conds = t_conds
        self.c_clip_seq = c_clip_seq
        if not isinstance(dropout, list):
            dropout = [dropout] * len(c_hidden)
        if not isinstance(self_attn, list):
            self_attn = [self_attn] * len(c_hidden)

        # CONDITIONING
        self.effnet_mapper = nn.Sequential(
            operations.Conv2d(c_effnet, c_hidden[0] * 4, kernel_size=1, dtype=dtype, device=device),
            nn.GELU(),
            operations.Conv2d(c_hidden[0] * 4, c_hidden[0], kernel_size=1, dtype=dtype, device=device),
            LayerNorm2d_op(operations)(c_hidden[0], elementwise_affine=False, eps=1e-6, dtype=dtype, device=device)
        )
        self.pixels_mapper = nn.Sequential(
            operations.Conv2d(c_pixels, c_hidden[0] * 4, kernel_size=1, dtype=dtype, device=device),
            nn.GELU(),
            operations.Conv2d(c_hidden[0] * 4, c_hidden[0], kernel_size=1, dtype=dtype, device=device),
            LayerNorm2d_op(operations)(c_hidden[0], elementwise_affine=False, eps=1e-6, dtype=dtype, device=device)
        )
        self.clip_mapper = operations.Linear(c_clip, c_cond * c_clip_seq, dtype=dtype, device=device)
        self.clip_norm = operations.LayerNorm(c_cond, elementwise_affine=False, eps=1e-6, dtype=dtype, device=device)

        self.embedding = nn.Sequential(
            nn.PixelUnshuffle(patch_size),
            operations.Conv2d(c_in * (patch_size ** 2), c_hidden[0], kernel_size=1, dtype=dtype, device=device),
            LayerNorm2d_op(operations)(c_hidden[0], elementwise_affine=False, eps=1e-6, dtype=dtype, device=device)
        )

        def get_block(block_type, c_hidden, nhead, c_skip=0, dropout=0, self_attn=True):
            if block_type == 'C':
                return ResBlock(c_hidden, c_skip, kernel_size=kernel_size, dropout=dropout, dtype=dtype, device=device, operations=operations)
            elif block_type == 'A':
                return AttnBlock(c_hidden, c_cond, nhead, self_attn=self_attn, dropout=dropout, dtype=dtype, device=device, operations=operations)
            elif block_type == 'F':
                return FeedForwardBlock(c_hidden, dropout=dropout, dtype=dtype, device=device, operations=operations)
            elif block_type == 'T':
                return TimestepBlock(c_hidden, c_r, conds=t_conds, dtype=dtype, device=device, operations=operations)
            else:
                raise Exception(f'Block type {block_type} not supported')

        # BLOCKS
        # -- down blocks
        self.down_blocks = nn.ModuleList()
        self.down_downscalers = nn.ModuleList()
        self.down_repeat_mappers = nn.ModuleList()
        for i in range(len(c_hidden)):
            if i > 0:
                self.down_downscalers.append(nn.Sequential(
                    LayerNorm2d_op(operations)(c_hidden[i - 1], elementwise_affine=False, eps=1e-6, dtype=dtype, device=device),
                    operations.Conv2d(c_hidden[i - 1], c_hidden[i], kernel_size=2, stride=2, dtype=dtype, device=device),
                ))
            else:
                self.down_downscalers.append(nn.Identity())
            down_block = nn.ModuleList()
            for _ in range(blocks[0][i]):
                for block_type in level_config[i]:
                    block = get_block(block_type, c_hidden[i], nhead[i], dropout=dropout[i], self_attn=self_attn[i])
                    down_block.append(block)
            self.down_blocks.append(down_block)
            if block_repeat is not None:
                block_repeat_mappers = nn.ModuleList()
                for _ in range(block_repeat[0][i] - 1):
                    block_repeat_mappers.append(operations.Conv2d(c_hidden[i], c_hidden[i], kernel_size=1, dtype=dtype, device=device))
                self.down_repeat_mappers.append(block_repeat_mappers)

        # -- up blocks
        self.up_blocks = nn.ModuleList()
        self.up_upscalers = nn.ModuleList()
        self.up_repeat_mappers = nn.ModuleList()
        for i in reversed(range(len(c_hidden))):
            if i > 0:
                self.up_upscalers.append(nn.Sequential(
                    LayerNorm2d_op(operations)(c_hidden[i], elementwise_affine=False, eps=1e-6, dtype=dtype, device=device),
                    operations.ConvTranspose2d(c_hidden[i], c_hidden[i - 1], kernel_size=2, stride=2, dtype=dtype, device=device),
                ))
            else:
                self.up_upscalers.append(nn.Identity())
            up_block = nn.ModuleList()
            for j in range(blocks[1][::-1][i]):
                for k, block_type in enumerate(level_config[i]):
                    c_skip = c_hidden[i] if i < len(c_hidden) - 1 and j == k == 0 else 0
                    block = get_block(block_type, c_hidden[i], nhead[i], c_skip=c_skip, dropout=dropout[i],
                                      self_attn=self_attn[i])
                    up_block.append(block)
            self.up_blocks.append(up_block)
            if block_repeat is not None:
                block_repeat_mappers = nn.ModuleList()
                for _ in range(block_repeat[1][::-1][i] - 1):
                    block_repeat_mappers.append(operations.Conv2d(c_hidden[i], c_hidden[i], kernel_size=1, dtype=dtype, device=device))
                self.up_repeat_mappers.append(block_repeat_mappers)

        # OUTPUT
        self.clf = nn.Sequential(
            LayerNorm2d_op(operations)(c_hidden[0], elementwise_affine=False, eps=1e-6, dtype=dtype, device=device),
            operations.Conv2d(c_hidden[0], c_out * (patch_size ** 2), kernel_size=1, dtype=dtype, device=device),
            nn.PixelShuffle(patch_size),
        )