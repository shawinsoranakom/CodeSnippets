def __init__(self, image_model=None, final_layer=True, dtype=None, device=None, operations=None, **kwargs):
        if operations is None:
            raise RuntimeError("Attempt to create ChromaRadiance object without setting operations")
        nn.Module.__init__(self)
        self.dtype = dtype
        params = ChromaRadianceParams(**kwargs)
        self.params = params
        self.patch_size = params.patch_size
        self.in_channels = params.in_channels
        self.out_channels = params.out_channels
        if params.hidden_size % params.num_heads != 0:
            raise ValueError(
                f"Hidden size {params.hidden_size} must be divisible by num_heads {params.num_heads}"
            )
        pe_dim = params.hidden_size // params.num_heads
        if sum(params.axes_dim) != pe_dim:
            raise ValueError(f"Got {params.axes_dim} but expected positional dim {pe_dim}")
        self.hidden_size = params.hidden_size
        self.num_heads = params.num_heads
        self.in_dim = params.in_dim
        self.out_dim = params.out_dim
        self.hidden_dim = params.hidden_dim
        self.n_layers = params.n_layers
        self.pe_embedder = EmbedND(dim=pe_dim, theta=params.theta, axes_dim=params.axes_dim)
        self.img_in_patch = operations.Conv2d(
            params.in_channels,
            params.hidden_size,
            kernel_size=params.patch_size,
            stride=params.patch_size,
            bias=True,
            dtype=dtype,
            device=device,
        )
        self.txt_in = operations.Linear(params.context_in_dim, self.hidden_size, dtype=dtype, device=device)
        # set as nn identity for now, will overwrite it later.
        self.distilled_guidance_layer = Approximator(
                    in_dim=self.in_dim,
                    hidden_dim=self.hidden_dim,
                    out_dim=self.out_dim,
                    n_layers=self.n_layers,
                    dtype=dtype, device=device, operations=operations
                )

        self.double_blocks = nn.ModuleList(
            [
                DoubleStreamBlock(
                    self.hidden_size,
                    self.num_heads,
                    mlp_ratio=params.mlp_ratio,
                    qkv_bias=params.qkv_bias,
                    modulation=False,
                    dtype=dtype, device=device, operations=operations
                )
                for _ in range(params.depth)
            ]
        )

        self.single_blocks = nn.ModuleList(
            [
                SingleStreamBlock(
                    self.hidden_size,
                    self.num_heads,
                    mlp_ratio=params.mlp_ratio,
                    modulation=False,
                    dtype=dtype, device=device, operations=operations,
                )
                for _ in range(params.depth_single_blocks)
            ]
        )

        # pixel channel concat with DCT
        self.nerf_image_embedder = NerfEmbedder(
            in_channels=params.in_channels,
            hidden_size_input=params.nerf_hidden_size,
            max_freqs=params.nerf_max_freqs,
            dtype=params.nerf_embedder_dtype or dtype,
            device=device,
            operations=operations,
        )

        self.nerf_blocks = nn.ModuleList([
            NerfGLUBlock(
                hidden_size_s=params.hidden_size,
                hidden_size_x=params.nerf_hidden_size,
                mlp_ratio=params.nerf_mlp_ratio,
                dtype=dtype,
                device=device,
                operations=operations,
            ) for _ in range(params.nerf_depth)
        ])

        if params.nerf_final_head_type == "linear":
            self.nerf_final_layer = NerfFinalLayer(
                params.nerf_hidden_size,
                out_channels=params.in_channels,
                dtype=dtype,
                device=device,
                operations=operations,
            )
        elif params.nerf_final_head_type == "conv":
            self.nerf_final_layer_conv = NerfFinalLayerConv(
                params.nerf_hidden_size,
                out_channels=params.in_channels,
                dtype=dtype,
                device=device,
                operations=operations,
            )
        else:
            errstr = f"Unsupported nerf_final_head_type {params.nerf_final_head_type}"
            raise ValueError(errstr)

        self.skip_mmdit = []
        self.skip_dit = []
        self.lite = False

        if params.use_x0:
            self.register_buffer("__x0__", torch.tensor([]))