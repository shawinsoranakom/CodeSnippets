def __init__(
        self,
        img_size: int = 224,
        in_chans: int = 3,
        num_classes: int = 1000,
        embed_dims: tuple[int, int, int, int] = (96, 192, 384, 768),
        depths: tuple[int, int, int, int] = (2, 2, 6, 2),
        num_heads: tuple[int, int, int, int] = (3, 6, 12, 24),
        window_sizes: tuple[int, int, int, int] = (7, 7, 14, 7),
        mlp_ratio: float = 4.0,
        drop_rate: float = 0.0,
        drop_path_rate: float = 0.1,
        use_checkpoint: bool = False,
        mbconv_expand_ratio: float = 4.0,
        local_conv_size: int = 3,
        layer_lr_decay: float = 1.0,
    ):
        """Initialize the TinyViT model.

        This constructor sets up the TinyViT architecture, including patch embedding, multiple layers of attention and
        convolution blocks, and a classification head.

        Args:
            img_size (int, optional): Size of the input image.
            in_chans (int, optional): Number of input channels.
            num_classes (int, optional): Number of classes for classification.
            embed_dims (tuple[int, int, int, int], optional): Embedding dimensions for each stage.
            depths (tuple[int, int, int, int], optional): Number of blocks in each stage.
            num_heads (tuple[int, int, int, int], optional): Number of attention heads in each stage.
            window_sizes (tuple[int, int, int, int], optional): Window sizes for each stage.
            mlp_ratio (float, optional): Ratio of MLP hidden dim to embedding dim.
            drop_rate (float, optional): Dropout rate.
            drop_path_rate (float, optional): Stochastic depth rate.
            use_checkpoint (bool, optional): Whether to use checkpointing to save memory.
            mbconv_expand_ratio (float, optional): Expansion ratio for MBConv layer.
            local_conv_size (int, optional): Kernel size for local convolutions.
            layer_lr_decay (float, optional): Layer-wise learning rate decay factor.
        """
        super().__init__()
        self.img_size = img_size
        self.num_classes = num_classes
        self.depths = depths
        self.num_layers = len(depths)
        self.mlp_ratio = mlp_ratio

        activation = nn.GELU

        self.patch_embed = PatchEmbed(
            in_chans=in_chans, embed_dim=embed_dims[0], resolution=img_size, activation=activation
        )

        patches_resolution = self.patch_embed.patches_resolution
        self.patches_resolution = patches_resolution

        # Stochastic depth
        dpr = [x.item() for x in torch.linspace(0, drop_path_rate, sum(depths))]  # stochastic depth decay rule

        # Build layers
        self.layers = nn.ModuleList()
        for i_layer in range(self.num_layers):
            kwargs = dict(
                dim=embed_dims[i_layer],
                input_resolution=(
                    patches_resolution[0] // (2 ** (i_layer - 1 if i_layer == 3 else i_layer)),
                    patches_resolution[1] // (2 ** (i_layer - 1 if i_layer == 3 else i_layer)),
                ),
                #   input_resolution=(patches_resolution[0] // (2 ** i_layer),
                #                     patches_resolution[1] // (2 ** i_layer)),
                depth=depths[i_layer],
                drop_path=dpr[sum(depths[:i_layer]) : sum(depths[: i_layer + 1])],
                downsample=PatchMerging if (i_layer < self.num_layers - 1) else None,
                use_checkpoint=use_checkpoint,
                out_dim=embed_dims[min(i_layer + 1, len(embed_dims) - 1)],
                activation=activation,
            )
            if i_layer == 0:
                layer = ConvLayer(conv_expand_ratio=mbconv_expand_ratio, **kwargs)
            else:
                layer = BasicLayer(
                    num_heads=num_heads[i_layer],
                    window_size=window_sizes[i_layer],
                    mlp_ratio=self.mlp_ratio,
                    drop=drop_rate,
                    local_conv_size=local_conv_size,
                    **kwargs,
                )
            self.layers.append(layer)

        # Classifier head
        self.norm_head = nn.LayerNorm(embed_dims[-1])
        self.head = nn.Linear(embed_dims[-1], num_classes) if num_classes > 0 else torch.nn.Identity()

        # Init weights
        self.apply(self._init_weights)
        self.set_layer_lr_decay(layer_lr_decay)
        self.neck = nn.Sequential(
            nn.Conv2d(
                embed_dims[-1],
                256,
                kernel_size=1,
                bias=False,
            ),
            LayerNorm2d(256),
            nn.Conv2d(
                256,
                256,
                kernel_size=3,
                padding=1,
                bias=False,
            ),
            LayerNorm2d(256),
        )