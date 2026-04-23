def __init__(self, image_model=None, final_layer=True, dtype=None, device=None, operations=None, **kwargs):
        super().__init__()
        self.dtype = dtype
        params = FluxParams(**kwargs)
        self.params = params
        self.patch_size = params.patch_size
        self.in_channels = params.in_channels * params.patch_size * params.patch_size
        self.out_channels = params.out_channels * params.patch_size * params.patch_size
        if params.hidden_size % params.num_heads != 0:
            raise ValueError(
                f"Hidden size {params.hidden_size} must be divisible by num_heads {params.num_heads}"
            )
        pe_dim = params.hidden_size // params.num_heads
        if sum(params.axes_dim) != pe_dim:
            raise ValueError(f"Got {params.axes_dim} but expected positional dim {pe_dim}")
        self.hidden_size = params.hidden_size
        self.num_heads = params.num_heads
        self.pe_embedder = EmbedND(dim=pe_dim, theta=params.theta, axes_dim=params.axes_dim)
        self.img_in = operations.Linear(self.in_channels, self.hidden_size, bias=params.ops_bias, dtype=dtype, device=device)
        self.time_in = MLPEmbedder(in_dim=256, hidden_dim=self.hidden_size, bias=params.ops_bias, dtype=dtype, device=device, operations=operations)
        if params.vec_in_dim is not None:
            self.vector_in = MLPEmbedder(params.vec_in_dim, self.hidden_size, dtype=dtype, device=device, operations=operations)
        else:
            self.vector_in = None

        self.guidance_in = (
            MLPEmbedder(in_dim=256, hidden_dim=self.hidden_size, bias=params.ops_bias, dtype=dtype, device=device, operations=operations) if params.guidance_embed else nn.Identity()
        )
        self.txt_in = operations.Linear(params.context_in_dim, self.hidden_size, bias=params.ops_bias, dtype=dtype, device=device)

        if params.txt_norm:
            self.txt_norm = operations.RMSNorm(params.context_in_dim, dtype=dtype, device=device)
        else:
            self.txt_norm = None

        self.double_blocks = nn.ModuleList(
            [
                DoubleStreamBlock(
                    self.hidden_size,
                    self.num_heads,
                    mlp_ratio=params.mlp_ratio,
                    qkv_bias=params.qkv_bias,
                    modulation=params.global_modulation is False,
                    mlp_silu_act=params.mlp_silu_act,
                    proj_bias=params.ops_bias,
                    yak_mlp=params.yak_mlp,
                    dtype=dtype, device=device, operations=operations
                )
                for _ in range(params.depth)
            ]
        )

        self.single_blocks = nn.ModuleList(
            [
                SingleStreamBlock(self.hidden_size, self.num_heads, mlp_ratio=params.mlp_ratio, modulation=params.global_modulation is False, mlp_silu_act=params.mlp_silu_act, bias=params.ops_bias, yak_mlp=params.yak_mlp, dtype=dtype, device=device, operations=operations)
                for _ in range(params.depth_single_blocks)
            ]
        )

        if final_layer:
            self.final_layer = LastLayer(self.hidden_size, 1, self.out_channels, bias=params.ops_bias, dtype=dtype, device=device, operations=operations)

        if params.global_modulation:
            self.double_stream_modulation_img = Modulation(
                self.hidden_size,
                double=True,
                bias=False,
                dtype=dtype, device=device, operations=operations
            )
            self.double_stream_modulation_txt = Modulation(
                self.hidden_size,
                double=True,
                bias=False,
                dtype=dtype, device=device, operations=operations
            )
            self.single_stream_modulation = Modulation(
                self.hidden_size, double=False, bias=False, dtype=dtype, device=device, operations=operations
            )