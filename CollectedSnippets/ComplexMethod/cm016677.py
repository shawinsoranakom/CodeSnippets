def __init__(
        self,
        dims,
        in_channels: int = 3,
        out_channels: int = 3,
        blocks: List[Tuple[str, int | dict]] = [("res_x", 1)],
        base_channels: int = 128,
        layers_per_block: int = 2,
        norm_num_groups: int = 32,
        patch_size: int = 1,
        norm_layer: str = "group_norm",
        causal: bool = True,
        timestep_conditioning: bool = False,
        spatial_padding_mode: str = "zeros",
    ):
        super().__init__()
        self.patch_size = patch_size
        self.layers_per_block = layers_per_block
        out_channels = out_channels * patch_size**2
        self.causal = causal
        self.blocks_desc = blocks

        # Compute output channel to be product of all channel-multiplier blocks
        output_channel = base_channels
        for block_name, block_params in list(reversed(blocks)):
            block_params = block_params if isinstance(block_params, dict) else {}
            if block_name == "res_x_y":
                output_channel = output_channel * block_params.get("multiplier", 2)
            if block_name == "compress_all":
                output_channel = output_channel * block_params.get("multiplier", 1)
            if block_name == "compress_space":
                output_channel = output_channel * block_params.get("multiplier", 1)
            if block_name == "compress_time":
                output_channel = output_channel * block_params.get("multiplier", 1)

        self.conv_in = make_conv_nd(
            dims,
            in_channels,
            output_channel,
            kernel_size=3,
            stride=1,
            padding=1,
            causal=True,
            spatial_padding_mode=spatial_padding_mode,
        )

        self.up_blocks = nn.ModuleList([])

        for block_name, block_params in list(reversed(blocks)):
            input_channel = output_channel
            if isinstance(block_params, int):
                block_params = {"num_layers": block_params}

            if block_name == "res_x":
                block = UNetMidBlock3D(
                    dims=dims,
                    in_channels=input_channel,
                    num_layers=block_params["num_layers"],
                    resnet_eps=1e-6,
                    resnet_groups=norm_num_groups,
                    norm_layer=norm_layer,
                    inject_noise=block_params.get("inject_noise", False),
                    timestep_conditioning=timestep_conditioning,
                    spatial_padding_mode=spatial_padding_mode,
                )
            elif block_name == "res_x_y":
                output_channel = output_channel // block_params.get("multiplier", 2)
                block = ResnetBlock3D(
                    dims=dims,
                    in_channels=input_channel,
                    out_channels=output_channel,
                    eps=1e-6,
                    groups=norm_num_groups,
                    norm_layer=norm_layer,
                    inject_noise=block_params.get("inject_noise", False),
                    timestep_conditioning=False,
                    spatial_padding_mode=spatial_padding_mode,
                )
            elif block_name == "compress_time":
                output_channel = output_channel // block_params.get("multiplier", 1)
                block = DepthToSpaceUpsample(
                    dims=dims,
                    in_channels=input_channel,
                    stride=(2, 1, 1),
                    out_channels_reduction_factor=block_params.get("multiplier", 1),
                    spatial_padding_mode=spatial_padding_mode,
                )
            elif block_name == "compress_space":
                output_channel = output_channel // block_params.get("multiplier", 1)
                block = DepthToSpaceUpsample(
                    dims=dims,
                    in_channels=input_channel,
                    stride=(1, 2, 2),
                    out_channels_reduction_factor=block_params.get("multiplier", 1),
                    spatial_padding_mode=spatial_padding_mode,
                )
            elif block_name == "compress_all":
                output_channel = output_channel // block_params.get("multiplier", 1)
                block = DepthToSpaceUpsample(
                    dims=dims,
                    in_channels=input_channel,
                    stride=(2, 2, 2),
                    residual=block_params.get("residual", False),
                    out_channels_reduction_factor=block_params.get("multiplier", 1),
                    spatial_padding_mode=spatial_padding_mode,
                )
            else:
                raise ValueError(f"unknown layer: {block_name}")

            self.up_blocks.append(block)

        if norm_layer == "group_norm":
            self.conv_norm_out = nn.GroupNorm(
                num_channels=output_channel, num_groups=norm_num_groups, eps=1e-6
            )
        elif norm_layer == "pixel_norm":
            self.conv_norm_out = PixelNorm()
        elif norm_layer == "layer_norm":
            self.conv_norm_out = LayerNorm(output_channel, eps=1e-6)

        self.conv_act = nn.SiLU()
        self.conv_out = make_conv_nd(
            dims,
            output_channel,
            out_channels,
            3,
            padding=1,
            causal=True,
            spatial_padding_mode=spatial_padding_mode,
        )

        self.gradient_checkpointing = False

        # Precompute output scale factors: (channels, (t_scale, h_scale, w_scale), t_offset)
        ts, hs, ws, to = 1, 1, 1, 0
        for block in self.up_blocks:
            if isinstance(block, DepthToSpaceUpsample):
                ts *= block.stride[0]
                hs *= block.stride[1]
                ws *= block.stride[2]
                if block.stride[0] > 1:
                    to = to * block.stride[0] + 1
        self._output_scale = (out_channels // (patch_size ** 2), (ts, hs * patch_size, ws * patch_size), to)

        self.timestep_conditioning = timestep_conditioning

        if timestep_conditioning:
            self.timestep_scale_multiplier = nn.Parameter(
                torch.tensor(1000.0, dtype=torch.float32)
            )
            self.last_time_embedder = PixArtAlphaCombinedTimestepSizeEmbeddings(
                output_channel * 2, 0, operations=ops,
            )
            self.last_scale_shift_table = nn.Parameter(torch.empty(2, output_channel))
        else:
            self.register_buffer(
                "last_scale_shift_table",
                torch.tensor(
                    [0.0, 0.0],
                    device="cpu" if in_meta_context() else None
                ).unsqueeze(1).expand(2, output_channel),
                persistent=False,
            )