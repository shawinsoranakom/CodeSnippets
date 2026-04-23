def __init__(
        self,
        embed_dim: int = 96,  # initial embed dim
        num_heads: int = 1,  # initial number of heads
        drop_path_rate: float = 0.0,  # stochastic depth
        q_pool: int = 3,  # number of q_pool stages
        q_stride: tuple[int, int] = (2, 2),  # downsample stride bet. stages
        stages: tuple[int, ...] = (2, 3, 16, 3),  # blocks per stage
        dim_mul: float = 2.0,  # dim_mul factor at stage shift
        head_mul: float = 2.0,  # head_mul factor at stage shift
        window_pos_embed_bkg_spatial_size: tuple[int, int] = (14, 14),
        # window size per stage, when not using global att.
        window_spec: tuple[int, ...] = (
            8,
            4,
            14,
            7,
        ),
        # global attn in these blocks
        global_att_blocks: tuple[int, ...] = (
            12,
            16,
            20,
        ),
        return_interm_layers=True,  # return feats from every stage
    ):
        """Initialize a Hiera model, a hierarchical vision transformer for efficient multiscale feature extraction.

        Hiera is a hierarchical vision transformer architecture designed for efficient multiscale feature extraction in
        image processing tasks. It uses a series of transformer blocks organized into stages, with optional pooling and
        global attention mechanisms.

        Args:
            embed_dim (int): Initial embedding dimension for the model.
            num_heads (int): Initial number of attention heads.
            drop_path_rate (float): Stochastic depth rate.
            q_pool (int): Number of query pooling stages.
            q_stride (tuple[int, int]): Downsampling stride between stages.
            stages (tuple[int, ...]): Number of blocks per stage.
            dim_mul (float): Dimension multiplier factor at stage transitions.
            head_mul (float): Head multiplier factor at stage transitions.
            window_pos_embed_bkg_spatial_size (tuple[int, int]): Spatial size for window positional embedding
                background.
            window_spec (tuple[int, ...]): Window sizes for each stage when not using global attention.
            global_att_blocks (tuple[int, ...]): Indices of blocks that use global attention.
            return_interm_layers (bool): Whether to return intermediate layer outputs.
        """
        super().__init__()

        assert len(stages) == len(window_spec)
        self.window_spec = window_spec

        depth = sum(stages)
        self.q_stride = q_stride
        self.stage_ends = [sum(stages[:i]) - 1 for i in range(1, len(stages) + 1)]
        assert 0 <= q_pool <= len(self.stage_ends[:-1])
        self.q_pool_blocks = [x + 1 for x in self.stage_ends[:-1]][:q_pool]
        self.return_interm_layers = return_interm_layers

        self.patch_embed = PatchEmbed(
            embed_dim=embed_dim,
            kernel_size=(7, 7),
            stride=(4, 4),
            padding=(3, 3),
        )
        # Which blocks have global attention?
        self.global_att_blocks = global_att_blocks

        # Windowed positional embedding (https://arxiv.org/abs/2311.05613)
        self.window_pos_embed_bkg_spatial_size = window_pos_embed_bkg_spatial_size
        self.pos_embed = nn.Parameter(torch.zeros(1, embed_dim, *self.window_pos_embed_bkg_spatial_size))
        self.pos_embed_window = nn.Parameter(torch.zeros(1, embed_dim, self.window_spec[0], self.window_spec[0]))

        dpr = [x.item() for x in torch.linspace(0, drop_path_rate, depth)]  # stochastic depth decay rule

        cur_stage = 1
        self.blocks = nn.ModuleList()

        for i in range(depth):
            dim_out = embed_dim
            # Lags by a block, so first block of next stage uses an initial window size
            # of previous stage and final window size of current stage
            window_size = self.window_spec[cur_stage - 1]

            if self.global_att_blocks is not None:
                window_size = 0 if i in self.global_att_blocks else window_size

            if i - 1 in self.stage_ends:
                dim_out = int(embed_dim * dim_mul)
                num_heads = int(num_heads * head_mul)
                cur_stage += 1

            block = MultiScaleBlock(
                dim=embed_dim,
                dim_out=dim_out,
                num_heads=num_heads,
                drop_path=dpr[i],
                q_stride=self.q_stride if i in self.q_pool_blocks else None,
                window_size=window_size,
            )

            embed_dim = dim_out
            self.blocks.append(block)

        self.channel_list = (
            [self.blocks[i].dim_out for i in self.stage_ends[::-1]]
            if return_interm_layers
            else [self.blocks[-1].dim_out]
        )