def __init__(
        self,
        patch_size: int = 2,
        in_channels: int = 4,
        dim: int = 4096,
        n_layers: int = 32,
        n_refiner_layers: int = 2,
        n_heads: int = 32,
        n_kv_heads: Optional[int] = None,
        multiple_of: int = 256,
        ffn_dim_multiplier: float = 4.0,
        norm_eps: float = 1e-5,
        qk_norm: bool = False,
        cap_feat_dim: int = 5120,
        axes_dims: List[int] = (16, 56, 56),
        axes_lens: List[int] = (1, 512, 512),
        rope_theta=10000.0,
        z_image_modulation=False,
        time_scale=1.0,
        pad_tokens_multiple=None,
        clip_text_dim=None,
        siglip_feat_dim=None,
        image_model=None,
        device=None,
        dtype=None,
        operations=None,
        **kwargs,
    ) -> None:
        super().__init__()
        self.dtype = dtype
        operation_settings = {"operations": operations, "device": device, "dtype": dtype}
        self.in_channels = in_channels
        self.out_channels = in_channels
        self.patch_size = patch_size
        self.time_scale = time_scale
        self.pad_tokens_multiple = pad_tokens_multiple

        self.x_embedder = operation_settings.get("operations").Linear(
            in_features=patch_size * patch_size * in_channels,
            out_features=dim,
            bias=True,
            device=operation_settings.get("device"),
            dtype=operation_settings.get("dtype"),
        )

        self.noise_refiner = nn.ModuleList(
            [
                JointTransformerBlock(
                    layer_id,
                    dim,
                    n_heads,
                    n_kv_heads,
                    multiple_of,
                    ffn_dim_multiplier,
                    norm_eps,
                    qk_norm,
                    modulation=True,
                    z_image_modulation=z_image_modulation,
                    operation_settings=operation_settings,
                )
                for layer_id in range(n_refiner_layers)
            ]
        )
        self.context_refiner = nn.ModuleList(
            [
                JointTransformerBlock(
                    layer_id,
                    dim,
                    n_heads,
                    n_kv_heads,
                    multiple_of,
                    ffn_dim_multiplier,
                    norm_eps,
                    qk_norm,
                    modulation=False,
                    operation_settings=operation_settings,
                )
                for layer_id in range(n_refiner_layers)
            ]
        )

        self.t_embedder = TimestepEmbedder(min(dim, 1024), output_size=256 if z_image_modulation else None, **operation_settings)
        self.cap_embedder = nn.Sequential(
            operation_settings.get("operations").RMSNorm(cap_feat_dim, eps=norm_eps, elementwise_affine=True, device=operation_settings.get("device"), dtype=operation_settings.get("dtype")),
            operation_settings.get("operations").Linear(
                cap_feat_dim,
                dim,
                bias=True,
                device=operation_settings.get("device"),
                dtype=operation_settings.get("dtype"),
            ),
        )

        self.clip_text_pooled_proj = None

        if clip_text_dim is not None:
            self.clip_text_dim = clip_text_dim
            self.clip_text_pooled_proj = nn.Sequential(
                operation_settings.get("operations").RMSNorm(clip_text_dim, eps=norm_eps, elementwise_affine=True, device=operation_settings.get("device"), dtype=operation_settings.get("dtype")),
                operation_settings.get("operations").Linear(
                    clip_text_dim,
                    clip_text_dim,
                    bias=True,
                    device=operation_settings.get("device"),
                    dtype=operation_settings.get("dtype"),
                ),
            )
            self.time_text_embed = nn.Sequential(
                nn.SiLU(),
                operation_settings.get("operations").Linear(
                    min(dim, 1024) + clip_text_dim,
                    min(dim, 1024),
                    bias=True,
                    device=operation_settings.get("device"),
                    dtype=operation_settings.get("dtype"),
                ),
            )

        self.layers = nn.ModuleList(
            [
                JointTransformerBlock(
                    layer_id,
                    dim,
                    n_heads,
                    n_kv_heads,
                    multiple_of,
                    ffn_dim_multiplier,
                    norm_eps,
                    qk_norm,
                    z_image_modulation=z_image_modulation,
                    attn_out_bias=False,
                    operation_settings=operation_settings,
                )
                for layer_id in range(n_layers)
            ]
        )

        if siglip_feat_dim is not None:
            self.siglip_embedder = nn.Sequential(
                operation_settings.get("operations").RMSNorm(siglip_feat_dim, eps=norm_eps, elementwise_affine=True, device=operation_settings.get("device"), dtype=operation_settings.get("dtype")),
                operation_settings.get("operations").Linear(
                    siglip_feat_dim,
                    dim,
                    bias=True,
                    device=operation_settings.get("device"),
                    dtype=operation_settings.get("dtype"),
                ),
            )
            self.siglip_refiner = nn.ModuleList(
                [
                    JointTransformerBlock(
                        layer_id,
                        dim,
                        n_heads,
                        n_kv_heads,
                        multiple_of,
                        ffn_dim_multiplier,
                        norm_eps,
                        qk_norm,
                        modulation=False,
                        operation_settings=operation_settings,
                    )
                    for layer_id in range(n_refiner_layers)
                ]
            )
            self.siglip_pad_token = nn.Parameter(torch.empty((1, dim), device=device, dtype=dtype))
        else:
            self.siglip_embedder = None
            self.siglip_refiner = None
            self.siglip_pad_token = None

        # This norm final is in the lumina 2.0 code but isn't actually used for anything.
        # self.norm_final = operation_settings.get("operations").RMSNorm(dim, eps=norm_eps, elementwise_affine=True, device=operation_settings.get("device"), dtype=operation_settings.get("dtype"))
        self.final_layer = FinalLayer(dim, patch_size, self.out_channels, z_image_modulation=z_image_modulation, operation_settings=operation_settings)

        if self.pad_tokens_multiple is not None:
            self.x_pad_token = nn.Parameter(torch.empty((1, dim), device=device, dtype=dtype))
            self.cap_pad_token = nn.Parameter(torch.empty((1, dim), device=device, dtype=dtype))

        assert (dim // n_heads) == sum(axes_dims)
        self.axes_dims = axes_dims
        self.axes_lens = axes_lens
        self.rope_embedder = EmbedND(dim=dim // n_heads, theta=rope_theta, axes_dim=axes_dims)
        self.dim = dim
        self.n_heads = n_heads