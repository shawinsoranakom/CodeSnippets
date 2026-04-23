def __init__(
        self,
        #  config: PretrainedConfig,
        patch_size: int,
        embed_dim: int,
        input_dims: input_dim_t,
        abs_pos: bool = True,
        normalize_patches: bool = False,
        cls_token: bool = False,
        max_input_dims: input_dim_t | None = None,
        pos_dropout: float = 0.0,
        return_pos_enc: bool = False,
        num_cls_tokens: int = 1,
        register_multiple: int | None = None,
        num_registers: int | None = None,
        patch_bias: bool = False,
        temporal_patch_size: int = 1,
        separate_video_embedder: bool = True,
        device=None,
        dtype=None,
    ):
        super().__init__()
        if isinstance(input_dims, int):
            input_dims = (input_dims, input_dims)

        if max_input_dims is None:
            max_input_dims = input_dims
        if isinstance(max_input_dims, int):
            max_input_dims = (max_input_dims, max_input_dims)

        max_input_dims = tuple(
            int(math.ceil(d / patch_size) * patch_size) for d in max_input_dims
        )

        self.cpe_mode = max_input_dims != input_dims
        self.pos_dropout = pos_dropout
        self.return_pos_enc = return_pos_enc

        factory = dict(device=device, dtype=dtype)

        self.patch_size = patch_size
        self.abs_pos = abs_pos
        self.embed_dim = embed_dim
        self.temporal_patch_size = temporal_patch_size

        self.num_rows = max_input_dims[0] // patch_size
        self.num_cols = max_input_dims[1] // patch_size
        self.input_dims = tuple(d // patch_size for d in input_dims)
        self.num_patches = self.num_rows * self.num_cols
        self.max_input_dims = max_input_dims

        self.im_to_patches = Im2Patches(patch_size)
        self.embedder = ViTPatchLinear(
            patch_size, embed_dim, bias=patch_bias, **factory
        )

        if temporal_patch_size > 1:
            if not separate_video_embedder:
                raise NotImplementedError(
                    "Only separate_video_embedder=True is supported for"
                    " temporal compression (temporal_patch_size > 1)"
                )
            self.video_embedder = ViTPatchLinear(
                patch_size,
                embed_dim,
                bias=patch_bias,
                temporal_patch_size=temporal_patch_size,
                **factory,
            )

        if abs_pos:
            scale = embed_dim**-0.5
            self.pos_embed = nn.Parameter(
                torch.randn(1, self.num_patches, embed_dim, **factory) * scale
            )

        self.cls_token = ClsToken(
            embed_dim,
            num_tokens=num_cls_tokens,
            enabled=cls_token,
            register_multiple=register_multiple,
            num_registers=num_registers,
        )

        self.patch_normalizer = (
            nn.LayerNorm(embed_dim) if normalize_patches else nn.Identity()
        )