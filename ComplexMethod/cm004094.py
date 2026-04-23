def __init__(self, config: ClapAudioConfig):
        super().__init__()
        img_size = (config.spec_size, config.spec_size) if isinstance(config.spec_size, int) else config.spec_size
        patch_size = (
            (config.patch_size, config.patch_size) if isinstance(config.patch_size, int) else config.patch_size
        )
        patch_stride = (
            (config.patch_stride, config.patch_stride) if isinstance(config.patch_stride, int) else config.patch_stride
        )

        self.img_size = img_size
        self.patch_stride = patch_stride

        self.grid_size = (img_size[0] // patch_stride[0], img_size[1] // patch_stride[1])
        self.num_patches = self.grid_size[0] * self.grid_size[1]

        self.flatten = config.flatten_patch_embeds
        self.enable_fusion = config.enable_fusion

        padding = ((patch_size[0] - patch_stride[0]) // 2, (patch_size[1] - patch_stride[1]) // 2)

        scale_factor = 4 if self.enable_fusion and config.fusion_type == "channel_map" else 1

        self.proj = nn.Conv2d(
            config.patch_embed_input_channels * scale_factor,
            config.patch_embeds_hidden_size,
            kernel_size=patch_size,
            stride=patch_stride,
            padding=padding,
        )

        self.norm = nn.LayerNorm(config.patch_embeds_hidden_size) if config.enable_patch_layer_norm else nn.Identity()
        if self.enable_fusion:
            self.fusion_model = ClapAudioAFFBlock(config)
            self.mel_conv2d = nn.Conv2d(
                config.patch_embed_input_channels,
                config.patch_embeds_hidden_size,
                kernel_size=(patch_size[0], patch_size[1] * 3),
                stride=(patch_stride[0], patch_stride[1] * 3),
                padding=padding,
            )