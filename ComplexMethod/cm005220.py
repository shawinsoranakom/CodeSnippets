def __init__(
        self,
        config: Sam2HieraDetConfig,
        stage_idx: int,
        block_idx: int,
        total_block_idx: int,
    ):
        super().__init__()

        # take embed dim from previous stage if first block of stage
        self.dim = (
            config.embed_dim_per_stage[stage_idx - 1]
            if stage_idx > 0 and block_idx == 0
            else config.embed_dim_per_stage[stage_idx]
        )
        self.dim_out = config.embed_dim_per_stage[stage_idx]
        self.layer_norm1 = nn.LayerNorm(self.dim, eps=config.layer_norm_eps)
        # take window size from previous stage if first block of stage
        self.window_size = (
            config.window_size_per_stage[stage_idx - 1]
            if stage_idx > 0 and block_idx == 0
            else config.window_size_per_stage[stage_idx]
        )
        self.window_size = 0 if total_block_idx in config.global_attention_blocks else self.window_size
        # use query stride for first block of stage if stage is a query pool stage
        self.query_stride = (
            config.query_stride if 0 < stage_idx <= config.num_query_pool_stages and block_idx == 0 else None
        )

        self.attn = Sam2MultiScaleAttention(
            config,
            self.dim,
            self.dim_out,
            num_attention_heads=config.num_attention_heads_per_stage[stage_idx],
            query_stride=self.query_stride,
        )
        self.layer_norm2 = nn.LayerNorm(self.dim_out, eps=config.layer_norm_eps)
        self.mlp = Sam2FeedForward(
            self.dim_out,
            int(self.dim_out * config.mlp_ratio),
            self.dim_out,
            num_layers=2,
            activation=config.hidden_act,
        )
        if self.dim != self.dim_out:
            self.proj = nn.Linear(self.dim, self.dim_out)