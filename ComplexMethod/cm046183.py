def __init__(
        self,
        img_size: int = 1024,
        patch_size: int = 16,
        in_chans: int = 3,
        embed_dim: int = 768,
        depth: int = 12,
        num_heads: int = 12,
        mlp_ratio: float = 4.0,
        qkv_bias: bool = True,
        drop_path_rate: float = 0.0,
        norm_layer: Callable[..., nn.Module] | str = "LayerNorm",
        act_layer: Callable[..., nn.Module] = nn.GELU,
        use_abs_pos: bool = True,
        tile_abs_pos: bool = True,
        rel_pos_blocks: tuple[int, ...] | bool = (2, 5, 8, 11),
        rel_pos_zero_init: bool = True,
        window_size: int = 14,
        global_att_blocks: tuple[int, ...] = (2, 5, 8, 11),
        use_rope: bool = False,
        rope_pt_size: int | None = None,
        use_interp_rope: bool = False,
        pretrain_img_size: int = 224,
        pretrain_use_cls_token: bool = True,
        retain_cls_token: bool = True,
        dropout: float = 0.0,
        return_interm_layers: bool = False,
        init_values: float | None = None,  # for layerscale
        ln_pre: bool = False,
        ln_post: bool = False,
        bias_patch_embed: bool = True,
        compile_mode: str | None = None,
        use_act_checkpoint: bool = True,
    ):
        """
        Args:
            img_size (int): Input image size. Only relevant for rel pos or rope.
            patch_size (int): Patch size.
            in_chans (int): Number of input image channels.
            embed_dim (int): Patch embedding dimension.
            depth (int): Depth of ViT.
            num_heads (int): Number of attention heads in each ViT block.
            mlp_ratio (float): Ratio of mlp hidden dim to embedding dim.
            qkv_bias (bool): If True, add a learnable bias to query, key, value.
            drop_path_rate (float): Stochastic depth rate.
            norm_layer (Callable or str): Normalization layer constructor or name.
            act_layer (Callable): Activation layer constructor.
            use_abs_pos (bool): If True, use absolute positional embeddings.
            tile_abs_pos (bool): If True, tile absolute positional embeddings instead of interpolation.
            rel_pos_blocks (tuple[int, ...] | bool): Blocks which have rel pos embeddings.
            rel_pos_zero_init (bool): If True, zero initialize relative positional parameters.
            window_size (int): Window size for window attention blocks.
            global_att_blocks (tuple[int, ...]): Indexes for blocks using global attention (other blocks use window
                attention).
            use_rope (bool): Whether to use rope 2d (independent of rel_pos_blocks, as it can be used together).
            rope_pt_size (int | None): Size of rope in previous stage of training, needed for interpolation or tiling.
            use_interp_rope (bool): Whether to interpolate (or extrapolate) rope to match target input size, expected to
                specify source size as rope_pt_size.
            pretrain_img_size (int): Input image size for pretraining models.
            pretrain_use_cls_token (bool): If True, pretraining models use class token.
            retain_cls_token (bool): Whether cls_token should be retained.
            dropout (float): Dropout rate. Applied in residual blocks of attn, mlp and inside the mlp.
            return_interm_layers (bool): Whether to return intermediate layers (all global attention blocks).
            init_values (float | None): Layer scale init, None for no layer scale.
            ln_pre (bool): If True, apply layer norm before transformer blocks.
            ln_post (bool): If True, apply layer norm after transformer blocks.
            bias_patch_embed (bool): If True, use bias in conv for patch embed.
            compile_mode (str | None): Mode to compile the forward, or None to disable.
            use_act_checkpoint (bool): If True, use activation checkpointing.
        """
        super().__init__()
        self.pretrain_use_cls_token = pretrain_use_cls_token

        window_block_indexes = [i for i in range(depth) if i not in global_att_blocks]
        self.full_attn_ids = list(global_att_blocks)
        self.rel_pos_blocks = [False] * depth
        if isinstance(rel_pos_blocks, bool) and rel_pos_blocks:
            self.rel_pos_blocks = [True] * depth
        else:
            for i in rel_pos_blocks:
                self.rel_pos_blocks[i] = True

        self.retain_cls_token = retain_cls_token
        if self.retain_cls_token:
            assert pretrain_use_cls_token
            assert len(window_block_indexes) == 0, "windowing not supported with cls token"

            assert sum(self.rel_pos_blocks) == 0, "rel pos not supported with cls token"

            scale = embed_dim**-0.5
            self.class_embedding = nn.Parameter(scale * torch.randn(1, 1, embed_dim))

        if isinstance(norm_layer, str):
            norm_layer = partial(getattr(nn, norm_layer), eps=1e-5)

        self.patch_embed = PatchEmbed(
            kernel_size=(patch_size, patch_size),
            stride=(patch_size, patch_size),
            in_chans=in_chans,
            embed_dim=embed_dim,
            bias=bias_patch_embed,
        )

        # Handle absolute positional embedding
        self.tile_abs_pos = tile_abs_pos
        self.use_abs_pos = use_abs_pos
        if self.tile_abs_pos:
            assert self.use_abs_pos

        if self.use_abs_pos:
            # Initialize absolute positional embedding with pretrain image size.
            num_patches = (pretrain_img_size // patch_size) * (pretrain_img_size // patch_size)
            num_positions = (num_patches + 1) if pretrain_use_cls_token else num_patches
            self.pos_embed = nn.Parameter(torch.zeros(1, num_positions, embed_dim))
        else:
            self.pos_embed = None

        # stochastic depth decay rule
        dpr = [x.item() for x in torch.linspace(0, drop_path_rate, depth)]

        self.patch_size = patch_size
        self.window_size = window_size
        self.blocks = nn.ModuleList()
        cur_stage = 1
        for i in range(depth):
            block = Block(
                dim=embed_dim,
                num_heads=num_heads,
                mlp_ratio=mlp_ratio,
                qkv_bias=qkv_bias,
                drop_path=dpr[i],
                norm_layer=norm_layer,
                act_layer=act_layer,
                use_rel_pos=self.rel_pos_blocks[i],
                rel_pos_zero_init=rel_pos_zero_init,
                window_size=window_size if i in window_block_indexes else 0,
                input_size=(img_size // patch_size, img_size // patch_size),
                use_rope=use_rope,
                rope_pt_size=((window_size, window_size) if rope_pt_size is None else (rope_pt_size, rope_pt_size)),
                rope_interp=use_interp_rope,
                cls_token=self.retain_cls_token,
                dropout=dropout,
                init_values=init_values,
            )

            if i not in window_block_indexes:
                cur_stage += 1

            self.use_act_checkpoint = use_act_checkpoint

            self.blocks.append(block)

        self.return_interm_layers = return_interm_layers
        self.channel_list = [embed_dim] * len(self.full_attn_ids) if return_interm_layers else [embed_dim]

        if self.pos_embed is not None:
            nn.init.trunc_normal_(self.pos_embed, std=0.02)

        self.ln_pre = norm_layer(embed_dim) if ln_pre else nn.Identity()
        self.ln_post = norm_layer(embed_dim) if ln_post else nn.Identity()

        self.apply(self._init_weights)

        if compile_mode is not None:
            self.forward = torch.compile(self.forward, mode=compile_mode, fullgraph=True)
            if self.use_act_checkpoint and self.training:
                torch._dynamo.config.optimize_ddp = False