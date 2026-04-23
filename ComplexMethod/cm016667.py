def __init__(
        self,
        in_channels: int = 128,
        mid_channels: int = 512,
        num_blocks_per_stage: int = 4,
        dims: int = 3,
        spatial_upsample: bool = True,
        temporal_upsample: bool = False,
        spatial_scale: float = 2.0,
        rational_resampler: bool = False,
    ):
        super().__init__()

        self.in_channels = in_channels
        self.mid_channels = mid_channels
        self.num_blocks_per_stage = num_blocks_per_stage
        self.dims = dims
        self.spatial_upsample = spatial_upsample
        self.temporal_upsample = temporal_upsample
        self.spatial_scale = float(spatial_scale)
        self.rational_resampler = rational_resampler

        Conv = nn.Conv2d if dims == 2 else nn.Conv3d

        self.initial_conv = Conv(in_channels, mid_channels, kernel_size=3, padding=1)
        self.initial_norm = nn.GroupNorm(32, mid_channels)
        self.initial_activation = nn.SiLU()

        self.res_blocks = nn.ModuleList(
            [ResBlock(mid_channels, dims=dims) for _ in range(num_blocks_per_stage)]
        )

        if spatial_upsample and temporal_upsample:
            self.upsampler = nn.Sequential(
                nn.Conv3d(mid_channels, 8 * mid_channels, kernel_size=3, padding=1),
                PixelShuffleND(3),
            )
        elif spatial_upsample:
            if rational_resampler:
                self.upsampler = SpatialRationalResampler(
                    mid_channels=mid_channels, scale=self.spatial_scale
                )
            else:
                self.upsampler = nn.Sequential(
                    nn.Conv2d(mid_channels, 4 * mid_channels, kernel_size=3, padding=1),
                    PixelShuffleND(2),
                )
        elif temporal_upsample:
            self.upsampler = nn.Sequential(
                nn.Conv3d(mid_channels, 2 * mid_channels, kernel_size=3, padding=1),
                PixelShuffleND(1),
            )
        else:
            raise ValueError(
                "Either spatial_upsample or temporal_upsample must be True"
            )

        self.post_upsample_res_blocks = nn.ModuleList(
            [ResBlock(mid_channels, dims=dims) for _ in range(num_blocks_per_stage)]
        )

        self.final_conv = Conv(mid_channels, in_channels, kernel_size=3, padding=1)