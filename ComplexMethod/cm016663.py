def __init__(
        self,
        *,
        out_channels: int = 3,
        latent_dim: int,
        base_channels: int,
        channel_multipliers: List[int],
        num_res_blocks: List[int],
        temporal_expansions: Optional[List[int]] = None,
        spatial_expansions: Optional[List[int]] = None,
        has_attention: List[bool],
        output_norm: bool = True,
        nonlinearity: str = "silu",
        output_nonlinearity: str = "silu",
        causal: bool = True,
        **block_kwargs,
    ):
        super().__init__()
        self.input_channels = latent_dim
        self.base_channels = base_channels
        self.channel_multipliers = channel_multipliers
        self.num_res_blocks = num_res_blocks
        self.output_nonlinearity = output_nonlinearity
        assert nonlinearity == "silu"
        assert causal

        ch = [mult * base_channels for mult in channel_multipliers]
        self.num_up_blocks = len(ch) - 1
        assert len(num_res_blocks) == self.num_up_blocks + 2

        blocks = []

        first_block = [
            ops.Conv3d(latent_dim, ch[-1], kernel_size=(1, 1, 1))
        ]  # Input layer.
        # First set of blocks preserve channel count.
        for _ in range(num_res_blocks[-1]):
            first_block.append(
                block_fn(
                    ch[-1],
                    has_attention=has_attention[-1],
                    causal=causal,
                    **block_kwargs,
                )
            )
        blocks.append(nn.Sequential(*first_block))

        assert len(temporal_expansions) == len(spatial_expansions) == self.num_up_blocks
        assert len(num_res_blocks) == len(has_attention) == self.num_up_blocks + 2

        upsample_block_fn = CausalUpsampleBlock

        for i in range(self.num_up_blocks):
            block = upsample_block_fn(
                ch[-i - 1],
                ch[-i - 2],
                num_res_blocks=num_res_blocks[-i - 2],
                has_attention=has_attention[-i - 2],
                temporal_expansion=temporal_expansions[-i - 1],
                spatial_expansion=spatial_expansions[-i - 1],
                causal=causal,
                **block_kwargs,
            )
            blocks.append(block)

        assert not output_norm

        # Last block. Preserve channel count.
        last_block = []
        for _ in range(num_res_blocks[0]):
            last_block.append(
                block_fn(
                    ch[0], has_attention=has_attention[0], causal=causal, **block_kwargs
                )
            )
        blocks.append(nn.Sequential(*last_block))

        self.blocks = nn.ModuleList(blocks)
        self.output_proj = Conv1x1(ch[0], out_channels)