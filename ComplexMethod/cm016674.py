def __init__(
        self,
        dims: Union[int, Tuple[int, int]] = 3,
        in_channels: int = 3,
        out_channels: int = 3,
        blocks: List[Tuple[str, int | dict]] = [("res_x", 1)],
        base_channels: int = 128,
        norm_num_groups: int = 32,
        patch_size: Union[int, Tuple[int]] = 1,
        norm_layer: str = "group_norm",  # group_norm, pixel_norm
        latent_log_var: str = "per_channel",
        spatial_padding_mode: str = "zeros",
    ):
        super().__init__()
        self.patch_size = patch_size
        self.norm_layer = norm_layer
        self.latent_channels = out_channels
        self.latent_log_var = latent_log_var
        self.blocks_desc = blocks

        in_channels = in_channels * patch_size**2
        output_channel = base_channels

        self.conv_in = make_conv_nd(
            dims=dims,
            in_channels=in_channels,
            out_channels=output_channel,
            kernel_size=3,
            stride=1,
            padding=1,
            causal=True,
            spatial_padding_mode=spatial_padding_mode,
        )

        self.down_blocks = nn.ModuleList([])

        for block_name, block_params in blocks:
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
                    spatial_padding_mode=spatial_padding_mode,
                )
            elif block_name == "res_x_y":
                output_channel = block_params.get("multiplier", 2) * output_channel
                block = ResnetBlock3D(
                    dims=dims,
                    in_channels=input_channel,
                    out_channels=output_channel,
                    eps=1e-6,
                    groups=norm_num_groups,
                    norm_layer=norm_layer,
                    spatial_padding_mode=spatial_padding_mode,
                )
            elif block_name == "compress_time":
                block = make_conv_nd(
                    dims=dims,
                    in_channels=input_channel,
                    out_channels=output_channel,
                    kernel_size=3,
                    stride=(2, 1, 1),
                    causal=True,
                    spatial_padding_mode=spatial_padding_mode,
                )
            elif block_name == "compress_space":
                block = make_conv_nd(
                    dims=dims,
                    in_channels=input_channel,
                    out_channels=output_channel,
                    kernel_size=3,
                    stride=(1, 2, 2),
                    causal=True,
                    spatial_padding_mode=spatial_padding_mode,
                )
            elif block_name == "compress_all":
                block = make_conv_nd(
                    dims=dims,
                    in_channels=input_channel,
                    out_channels=output_channel,
                    kernel_size=3,
                    stride=(2, 2, 2),
                    causal=True,
                    spatial_padding_mode=spatial_padding_mode,
                )
            elif block_name == "compress_all_x_y":
                output_channel = block_params.get("multiplier", 2) * output_channel
                block = make_conv_nd(
                    dims=dims,
                    in_channels=input_channel,
                    out_channels=output_channel,
                    kernel_size=3,
                    stride=(2, 2, 2),
                    causal=True,
                    spatial_padding_mode=spatial_padding_mode,
                )
            elif block_name == "compress_all_res":
                output_channel = block_params.get("multiplier", 2) * output_channel
                block = SpaceToDepthDownsample(
                    dims=dims,
                    in_channels=input_channel,
                    out_channels=output_channel,
                    stride=(2, 2, 2),
                    spatial_padding_mode=spatial_padding_mode,
                )
            elif block_name == "compress_space_res":
                output_channel = block_params.get("multiplier", 2) * output_channel
                block = SpaceToDepthDownsample(
                    dims=dims,
                    in_channels=input_channel,
                    out_channels=output_channel,
                    stride=(1, 2, 2),
                    spatial_padding_mode=spatial_padding_mode,
                )
            elif block_name == "compress_time_res":
                output_channel = block_params.get("multiplier", 2) * output_channel
                block = SpaceToDepthDownsample(
                    dims=dims,
                    in_channels=input_channel,
                    out_channels=output_channel,
                    stride=(2, 1, 1),
                    spatial_padding_mode=spatial_padding_mode,
                )
            else:
                raise ValueError(f"unknown block: {block_name}")

            self.down_blocks.append(block)

        # out
        if norm_layer == "group_norm":
            self.conv_norm_out = nn.GroupNorm(
                num_channels=output_channel, num_groups=norm_num_groups, eps=1e-6
            )
        elif norm_layer == "pixel_norm":
            self.conv_norm_out = PixelNorm()
        elif norm_layer == "layer_norm":
            self.conv_norm_out = LayerNorm(output_channel, eps=1e-6)

        self.conv_act = nn.SiLU()

        conv_out_channels = out_channels
        if latent_log_var == "per_channel":
            conv_out_channels *= 2
        elif latent_log_var == "uniform":
            conv_out_channels += 1
        elif latent_log_var == "constant":
            conv_out_channels += 1
        elif latent_log_var != "none":
            raise ValueError(f"Invalid latent_log_var: {latent_log_var}")
        self.conv_out = make_conv_nd(
            dims,
            output_channel,
            conv_out_channels,
            3,
            padding=1,
            causal=True,
            spatial_padding_mode=spatial_padding_mode,
        )

        self.gradient_checkpointing = False