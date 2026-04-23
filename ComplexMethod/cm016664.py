def __init__(
        self,
        *,
        in_channels: int,
        base_channels: int,
        channel_multipliers: List[int],
        num_res_blocks: List[int],
        latent_dim: int,
        temporal_reductions: List[int],
        spatial_reductions: List[int],
        prune_bottlenecks: List[bool],
        has_attentions: List[bool],
        affine: bool = True,
        bias: bool = True,
        input_is_conv_1x1: bool = False,
        padding_mode: str,
    ):
        super().__init__()
        self.temporal_reductions = temporal_reductions
        self.spatial_reductions = spatial_reductions
        self.base_channels = base_channels
        self.channel_multipliers = channel_multipliers
        self.num_res_blocks = num_res_blocks
        self.latent_dim = latent_dim

        self.fourier_features = FourierFeatures()
        ch = [mult * base_channels for mult in channel_multipliers]
        num_down_blocks = len(ch) - 1
        assert len(num_res_blocks) == num_down_blocks + 2

        layers = (
            [ops.Conv3d(in_channels, ch[0], kernel_size=(1, 1, 1), bias=True)]
            if not input_is_conv_1x1
            else [Conv1x1(in_channels, ch[0])]
        )

        assert len(prune_bottlenecks) == num_down_blocks + 2
        assert len(has_attentions) == num_down_blocks + 2
        block = partial(block_fn, padding_mode=padding_mode, affine=affine, bias=bias)

        for _ in range(num_res_blocks[0]):
            layers.append(block(ch[0], has_attention=has_attentions[0], prune_bottleneck=prune_bottlenecks[0]))
        prune_bottlenecks = prune_bottlenecks[1:]
        has_attentions = has_attentions[1:]

        assert len(temporal_reductions) == len(spatial_reductions) == len(ch) - 1
        for i in range(num_down_blocks):
            layer = DownsampleBlock(
                ch[i],
                ch[i + 1],
                num_res_blocks=num_res_blocks[i + 1],
                temporal_reduction=temporal_reductions[i],
                spatial_reduction=spatial_reductions[i],
                prune_bottleneck=prune_bottlenecks[i],
                has_attention=has_attentions[i],
                affine=affine,
                bias=bias,
                padding_mode=padding_mode,
            )

            layers.append(layer)

        # Additional blocks.
        for _ in range(num_res_blocks[-1]):
            layers.append(block(ch[-1], has_attention=has_attentions[-1], prune_bottleneck=prune_bottlenecks[-1]))

        self.layers = nn.Sequential(*layers)

        # Output layers.
        self.output_norm = norm_fn(ch[-1])
        self.output_proj = Conv1x1(ch[-1], 2 * latent_dim, bias=False)