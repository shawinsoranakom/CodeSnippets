def __init__(
        self,
        config,
        prep_type="conv",
        spatial_downsample: int = 4,
        temporal_downsample: int = 1,
        position_encoding_type: str = "fourier",
        in_channels: int = 3,
        out_channels: int = 64,
        conv_after_patching: bool = False,
        conv_after_patching_in_channels: int = 54,  # only relevant when conv_after_patching = True
        conv2d_use_batchnorm: bool = True,
        concat_or_add_pos: str = "concat",
        project_pos_dim: int = -1,
        **position_encoding_kwargs,
    ):
        super().__init__()
        self.config = config

        if prep_type not in ("conv", "patches", "pixels", "conv1x1"):
            raise ValueError(f"Prep_type {prep_type} is invalid")

        if concat_or_add_pos not in ["concat", "add"]:
            raise ValueError(f"Invalid value {concat_or_add_pos} for concat_or_add_pos.")

        self.in_channels = in_channels
        self.prep_type = prep_type
        self.spatial_downsample = spatial_downsample
        self.temporal_downsample = temporal_downsample
        self.position_encoding_type = position_encoding_type
        self.concat_or_add_pos = concat_or_add_pos
        self.conv_after_patching = conv_after_patching
        self.out_channels = out_channels

        if self.prep_type == "conv":
            # Downsampling with conv is currently restricted
            convnet_num_layers = math.log(spatial_downsample, 4)
            convnet_num_layers_is_int = convnet_num_layers == np.round(convnet_num_layers)
            if not convnet_num_layers_is_int or temporal_downsample != 1:
                raise ValueError(
                    "Only powers of 4 expected for spatial and 1 expected for temporal downsampling with conv."
                )
            self.convnet = Conv2DDownsample(
                in_channels=in_channels,
                num_layers=int(convnet_num_layers),
                out_channels=out_channels,
                use_batchnorm=conv2d_use_batchnorm,
            )

        elif self.prep_type == "conv1x1":
            if temporal_downsample != 1:
                raise ValueError("Conv1x1 does not downsample in time.")
            self.convnet_1x1 = nn.Conv2d(
                in_channels=in_channels,
                out_channels=out_channels,
                kernel_size=(1, 1),
                # spatial_downsample is unconstrained for 1x1 convolutions.
                stride=(spatial_downsample, spatial_downsample),
            )

        # Position embeddings
        self.project_pos_dim = project_pos_dim
        self.position_embeddings, self.positions_projection = build_position_encoding(
            position_encoding_type=position_encoding_type,
            out_channels=out_channels,
            project_pos_dim=project_pos_dim,
            **position_encoding_kwargs,
        )

        # Optional convolutional layer after patches.
        self.conv_after_patches = (
            nn.Linear(conv_after_patching_in_channels, self.out_channels) if conv_after_patching else nn.Identity()
        )