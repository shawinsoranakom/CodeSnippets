def __init__(
        self,
        input_size: int = 32,
        patch_size: int = 2,
        in_channels: int = 4,
        depth: int = 28,
        # hidden_size: Optional[int] = None,
        # num_heads: Optional[int] = None,
        mlp_ratio: float = 4.0,
        learn_sigma: bool = False,
        adm_in_channels: Optional[int] = None,
        context_embedder_config: Optional[Dict] = None,
        compile_core: bool = False,
        use_checkpoint: bool = False,
        register_length: int = 0,
        attn_mode: str = "torch",
        rmsnorm: bool = False,
        scale_mod_only: bool = False,
        swiglu: bool = False,
        out_channels: Optional[int] = None,
        pos_embed_scaling_factor: Optional[float] = None,
        pos_embed_offset: Optional[float] = None,
        pos_embed_max_size: Optional[int] = None,
        num_patches = None,
        qk_norm: Optional[str] = None,
        qkv_bias: bool = True,
        context_processor_layers = None,
        x_block_self_attn: bool = False,
        x_block_self_attn_layers: Optional[List[int]] = [],
        context_size = 4096,
        num_blocks = None,
        final_layer = True,
        skip_blocks = False,
        dtype = None, #TODO
        device = None,
        operations = None,
    ):
        super().__init__()
        self.dtype = dtype
        self.learn_sigma = learn_sigma
        self.in_channels = in_channels
        default_out_channels = in_channels * 2 if learn_sigma else in_channels
        self.out_channels = default(out_channels, default_out_channels)
        self.patch_size = patch_size
        self.pos_embed_scaling_factor = pos_embed_scaling_factor
        self.pos_embed_offset = pos_embed_offset
        self.pos_embed_max_size = pos_embed_max_size
        self.x_block_self_attn_layers = x_block_self_attn_layers

        # hidden_size = default(hidden_size, 64 * depth)
        # num_heads = default(num_heads, hidden_size // 64)

        # apply magic --> this defines a head_size of 64
        self.hidden_size = 64 * depth
        num_heads = depth
        if num_blocks is None:
            num_blocks = depth

        self.depth = depth
        self.num_heads = num_heads

        self.x_embedder = PatchEmbed(
            input_size,
            patch_size,
            in_channels,
            self.hidden_size,
            bias=True,
            strict_img_size=self.pos_embed_max_size is None,
            dtype=dtype,
            device=device,
            operations=operations
        )
        self.t_embedder = TimestepEmbedder(self.hidden_size, dtype=dtype, device=device, operations=operations)

        self.y_embedder = None
        if adm_in_channels is not None:
            assert isinstance(adm_in_channels, int)
            self.y_embedder = VectorEmbedder(adm_in_channels, self.hidden_size, dtype=dtype, device=device, operations=operations)

        if context_processor_layers is not None:
            self.context_processor = ContextProcessor(context_size, context_processor_layers, dtype=dtype, device=device, operations=operations)
        else:
            self.context_processor = None

        self.context_embedder = nn.Identity()
        if context_embedder_config is not None:
            if context_embedder_config["target"] == "torch.nn.Linear":
                self.context_embedder = operations.Linear(**context_embedder_config["params"], dtype=dtype, device=device)

        self.register_length = register_length
        if self.register_length > 0:
            self.register = nn.Parameter(torch.randn(1, register_length, self.hidden_size, dtype=dtype, device=device))

        # num_patches = self.x_embedder.num_patches
        # Will use fixed sin-cos embedding:
        # just use a buffer already
        if num_patches is not None:
            self.register_buffer(
                "pos_embed",
                torch.empty(1, num_patches, self.hidden_size, dtype=dtype, device=device),
            )
        else:
            self.pos_embed = None

        self.use_checkpoint = use_checkpoint
        if not skip_blocks:
            self.joint_blocks = nn.ModuleList(
                [
                    JointBlock(
                        self.hidden_size,
                        num_heads,
                        mlp_ratio=mlp_ratio,
                        qkv_bias=qkv_bias,
                        attn_mode=attn_mode,
                        pre_only=(i == num_blocks - 1) and final_layer,
                        rmsnorm=rmsnorm,
                        scale_mod_only=scale_mod_only,
                        swiglu=swiglu,
                        qk_norm=qk_norm,
                        x_block_self_attn=(i in self.x_block_self_attn_layers) or x_block_self_attn,
                        dtype=dtype,
                        device=device,
                        operations=operations,
                    )
                    for i in range(num_blocks)
                ]
            )

        if final_layer:
            self.final_layer = FinalLayer(self.hidden_size, patch_size, self.out_channels, dtype=dtype, device=device, operations=operations)

        if compile_core:
            assert False
            self.forward_core_with_concat = torch.compile(self.forward_core_with_concat)