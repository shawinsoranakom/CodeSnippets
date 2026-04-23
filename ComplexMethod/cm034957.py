def __init__(
        self,
        backbone_layers=[2, 3, 7],
        input_channel=1,
        is_predict=False,
        is_export=False,
        img_size=(224, 224),
        patch_size=16,
        num_classes=1000,
        embed_dim=768,
        depth=12,
        num_heads=12,
        mlp_ratio=4.0,
        qkv_bias=True,
        representation_size=None,
        distilled=False,
        drop_rate=0.0,
        attn_drop_rate=0.0,
        drop_path_rate=0.0,
        embed_layer=None,
        norm_layer=None,
        act_layer=None,
        weight_init="",
        **kwargs,
    ):
        super(HybridTransformer, self).__init__()
        self.num_classes = num_classes
        self.num_features = self.embed_dim = (
            embed_dim  # num_features for consistency with other models
        )
        self.num_tokens = 2 if distilled else 1
        norm_layer = norm_layer or partial(nn.LayerNorm, epsilon=1e-6)
        act_layer = act_layer or nn.GELU
        self.height, self.width = img_size
        self.patch_size = patch_size
        backbone = ResNetV2(
            layers=backbone_layers,
            num_classes=0,
            global_pool="",
            in_chans=input_channel,
            preact=False,
            stem_type="same",
            conv_layer=StdConv2dSame,
            is_export=is_export,
        )
        min_patch_size = 2 ** (len(backbone_layers) + 1)
        self.patch_embed = HybridEmbed(
            img_size=img_size,
            patch_size=patch_size // min_patch_size,
            in_chans=input_channel,
            embed_dim=embed_dim,
            backbone=backbone,
        )
        num_patches = self.patch_embed.num_patches

        self.cls_token = paddle.create_parameter([1, 1, embed_dim], dtype="float32")
        self.dist_token = (
            paddle.create_parameter(
                [1, 1, embed_dim],
                dtype="float32",
            )
            if distilled
            else None
        )
        self.pos_embed = paddle.create_parameter(
            [1, num_patches + self.num_tokens, embed_dim], dtype="float32"
        )
        self.pos_drop = nn.Dropout(p=drop_rate)
        zeros_(self.cls_token)
        if self.dist_token is not None:
            zeros_(self.dist_token)
        zeros_(self.pos_embed)

        dpr = [
            x.item() for x in paddle.linspace(0, drop_path_rate, depth)
        ]  # stochastic depth decay rule
        self.blocks = nn.Sequential(
            *[
                Block(
                    dim=embed_dim,
                    num_heads=num_heads,
                    mlp_ratio=mlp_ratio,
                    qkv_bias=qkv_bias,
                    drop=drop_rate,
                    attn_drop=attn_drop_rate,
                    drop_path=dpr[i],
                    norm_layer=norm_layer,
                    act_layer=act_layer,
                )
                for i in range(depth)
            ]
        )
        self.norm = norm_layer(embed_dim)

        # Representation layer
        if representation_size and not distilled:
            self.num_features = representation_size
            self.pre_logits = nn.Sequential(
                ("fc", nn.Linear(embed_dim, representation_size)), ("act", nn.Tanh())
            )
        else:
            self.pre_logits = nn.Identity()

        # Classifier head(s)
        self.head = (
            nn.Linear(self.num_features, num_classes)
            if num_classes > 0
            else nn.Identity()
        )
        self.head_dist = None
        if distilled:
            self.head_dist = (
                nn.Linear(self.embed_dim, self.num_classes)
                if num_classes > 0
                else nn.Identity()
            )
        self.init_weights(weight_init)
        self.out_channels = embed_dim
        self.is_predict = is_predict
        self.is_export = is_export