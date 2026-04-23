def __init__(self, image_model=None, final_layer=True, dtype=None, device=None, operations=None, **kwargs):
        super().__init__()
        self.dtype = dtype
        operation_settings = {"operations": operations, "device": device, "dtype": dtype}

        params = HunyuanVideoParams(**kwargs)
        self.params = params
        self.patch_size = params.patch_size
        self.in_channels = params.in_channels
        self.out_channels = params.out_channels
        self.use_cond_type_embedding = params.use_cond_type_embedding
        self.vision_in_dim = params.vision_in_dim
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

        self.img_in = comfy.ldm.modules.diffusionmodules.mmdit.PatchEmbed(None, self.patch_size, self.in_channels, self.hidden_size, conv3d=len(self.patch_size) == 3, dtype=dtype, device=device, operations=operations)
        self.time_in = MLPEmbedder(in_dim=256, hidden_dim=self.hidden_size, dtype=dtype, device=device, operations=operations)
        if params.vec_in_dim is not None:
            self.vector_in = MLPEmbedder(params.vec_in_dim, self.hidden_size, dtype=dtype, device=device, operations=operations)
        else:
            self.vector_in = None

        self.guidance_in = (
            MLPEmbedder(in_dim=256, hidden_dim=self.hidden_size, dtype=dtype, device=device, operations=operations) if params.guidance_embed else nn.Identity()
        )

        self.txt_in = TokenRefiner(params.context_in_dim, self.hidden_size, self.num_heads, 2, dtype=dtype, device=device, operations=operations)

        self.double_blocks = nn.ModuleList(
            [
                DoubleStreamBlock(
                    self.hidden_size,
                    self.num_heads,
                    mlp_ratio=params.mlp_ratio,
                    qkv_bias=params.qkv_bias,
                    dtype=dtype, device=device, operations=operations
                )
                for _ in range(params.depth)
            ]
        )

        self.single_blocks = nn.ModuleList(
            [
                SingleStreamBlock(self.hidden_size, self.num_heads, mlp_ratio=params.mlp_ratio, dtype=dtype, device=device, operations=operations)
                for _ in range(params.depth_single_blocks)
            ]
        )

        if params.byt5:
            self.byt5_in = ByT5Mapper(
                in_dim=1472,
                out_dim=2048,
                hidden_dim=2048,
                out_dim1=self.hidden_size,
                use_res=False,
                dtype=dtype, device=device, operations=operations
            )
        else:
            self.byt5_in = None

        if params.meanflow:
            self.time_r_in = MLPEmbedder(in_dim=256, hidden_dim=self.hidden_size, dtype=dtype, device=device, operations=operations)
        else:
            self.time_r_in = None

        if final_layer:
            self.final_layer = LastLayer(self.hidden_size, self.patch_size[-1], self.out_channels, dtype=dtype, device=device, operations=operations)

        # HunyuanVideo 1.5 specific modules
        if self.vision_in_dim is not None:
            from comfy.ldm.wan.model import MLPProj
            self.vision_in = MLPProj(in_dim=self.vision_in_dim, out_dim=self.hidden_size, operation_settings=operation_settings)
        else:
            self.vision_in = None
        if self.use_cond_type_embedding:
            # 0: text_encoder feature 1: byt5 feature 2: vision_encoder feature
            self.cond_type_embedding = nn.Embedding(3, self.hidden_size)
        else:
            self.cond_type_embedding = None