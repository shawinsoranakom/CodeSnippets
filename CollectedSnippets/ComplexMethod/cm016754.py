def __init__(
        self,
        out_channels: int,
        channels: int,
        channels_mult: list[int],
        num_res_blocks: int,
        attn_resolutions: list[int],
        dropout: float,
        resolution: int,
        z_channels: int,
        spatial_compression: int = 8,
        temporal_compression: int = 8,
        **ignore_kwargs,
    ):
        super().__init__()
        self.num_resolutions = len(channels_mult)
        self.num_res_blocks = num_res_blocks

        # UnPatcher.
        patch_size = ignore_kwargs.get("patch_size", 1)
        self.unpatcher3d = UnPatcher3D(
            patch_size, ignore_kwargs.get("patch_method", "haar")
        )
        out_ch = out_channels * patch_size * patch_size * patch_size

        # calculate the number of upsample operations
        self.num_spatial_ups = int(math.log2(spatial_compression)) - int(
            math.log2(patch_size)
        )
        assert (
            self.num_spatial_ups <= self.num_resolutions
        ), f"Spatially upsample {self.num_resolutions} times at most"
        self.num_temporal_ups = int(math.log2(temporal_compression)) - int(
            math.log2(patch_size)
        )
        assert (
            self.num_temporal_ups <= self.num_resolutions
        ), f"Temporally upsample {self.num_resolutions} times at most"

        block_in = channels * channels_mult[self.num_resolutions - 1]
        curr_res = (resolution // patch_size) // 2 ** (self.num_resolutions - 1)
        self.z_shape = (1, z_channels, curr_res, curr_res)
        logging.debug(
            "Working with z of shape {} = {} dimensions.".format(
                self.z_shape, np.prod(self.z_shape)
            )
        )

        # z to block_in
        self.conv_in = nn.Sequential(
            CausalConv3d(
                z_channels, block_in, kernel_size=(1, 3, 3), stride=1, padding=1
            ),
            CausalConv3d(
                block_in, block_in, kernel_size=(3, 1, 1), stride=1, padding=0
            ),
        )

        # middle
        self.mid = nn.Module()
        self.mid.block_1 = CausalResnetBlockFactorized3d(
            in_channels=block_in,
            out_channels=block_in,
            dropout=dropout,
            num_groups=1,
        )
        self.mid.attn_1 = nn.Sequential(
            CausalAttnBlock(block_in, num_groups=1),
            CausalTemporalAttnBlock(block_in, num_groups=1),
        )
        self.mid.block_2 = CausalResnetBlockFactorized3d(
            in_channels=block_in,
            out_channels=block_in,
            dropout=dropout,
            num_groups=1,
        )

        legacy_mode = ignore_kwargs.get("legacy_mode", False)
        # upsampling
        self.up = nn.ModuleList()
        for i_level in reversed(range(self.num_resolutions)):
            block = nn.ModuleList()
            attn = nn.ModuleList()
            block_out = channels * channels_mult[i_level]
            for _ in range(self.num_res_blocks + 1):
                block.append(
                    CausalResnetBlockFactorized3d(
                        in_channels=block_in,
                        out_channels=block_out,
                        dropout=dropout,
                        num_groups=1,
                    )
                )
                block_in = block_out
                if curr_res in attn_resolutions:
                    attn.append(
                        nn.Sequential(
                            CausalAttnBlock(block_in, num_groups=1),
                            CausalTemporalAttnBlock(block_in, num_groups=1),
                        )
                    )
            up = nn.Module()
            up.block = block
            up.attn = attn
            if i_level != 0:
                # The layer index for temporal/spatial downsampling performed
                # in the encoder should correspond to the layer index in
                # reverse order where upsampling is performed in the decoder.
                # If you've a pre-trained model, you can simply finetune.
                i_level_reverse = self.num_resolutions - i_level - 1
                if legacy_mode:
                    temporal_up = i_level_reverse < self.num_temporal_ups
                else:
                    temporal_up = 0 < i_level_reverse < self.num_temporal_ups + 1
                spatial_up = temporal_up or (
                    i_level_reverse < self.num_spatial_ups
                    and self.num_spatial_ups > self.num_temporal_ups
                )
                up.upsample = CausalHybridUpsample3d(
                    block_in, spatial_up=spatial_up, temporal_up=temporal_up
                )
                curr_res = curr_res * 2
            self.up.insert(0, up)  # prepend to get consistent order

        # end
        self.norm_out = CausalNormalize(block_in, num_groups=1)
        self.conv_out = nn.Sequential(
            CausalConv3d(block_in, out_ch, kernel_size=(1, 3, 3), stride=1, padding=1),
            CausalConv3d(out_ch, out_ch, kernel_size=(3, 1, 1), stride=1, padding=0),
        )