def __init__(
        self,
        img_size=[32, 100],
        in_channels=3,
        embed_dim=[64, 128, 256],
        depth=[3, 6, 3],
        num_heads=[2, 4, 8],
        mixer=["Local"] * 6 + ["Global"] * 6,  # Local atten, Global atten, Conv
        local_mixer=[[7, 11], [7, 11], [7, 11]],
        patch_merging="Conv",  # Conv, Pool, None
        mlp_ratio=4,
        qkv_bias=True,
        qk_scale=None,
        drop_rate=0.0,
        last_drop=0.0,
        attn_drop_rate=0.0,
        drop_path_rate=0.1,
        norm_layer="nn.LayerNorm",
        sub_norm="nn.LayerNorm",
        epsilon=1e-6,
        out_channels=192,
        out_char_num=25,
        block_unit="Block",
        act="gelu",
        last_stage=True,
        sub_num=2,
        prenorm=True,
        use_lenhead=False,
        **kwargs
    ):
        super().__init__()
        self.img_size = img_size
        self.embed_dim = embed_dim
        self.out_channels = out_channels
        self.prenorm = prenorm
        patch_merging = (
            None
            if patch_merging != "Conv" and patch_merging != "Pool"
            else patch_merging
        )
        self.patch_embed = PatchEmbed(
            img_size=img_size,
            in_channels=in_channels,
            embed_dim=embed_dim[0],
            sub_num=sub_num,
        )
        num_patches = self.patch_embed.num_patches
        self.HW = [img_size[0] // (2**sub_num), img_size[1] // (2**sub_num)]
        self.pos_embed = nn.Parameter(torch.zeros(1, num_patches, embed_dim[0]))
        self.pos_drop = nn.Dropout(p=drop_rate)
        Block_unit = eval(block_unit)

        dpr = np.linspace(0, drop_path_rate, sum(depth))
        self.blocks1 = nn.ModuleList(
            [
                Block_unit(
                    dim=embed_dim[0],
                    num_heads=num_heads[0],
                    mixer=mixer[0 : depth[0]][i],
                    HW=self.HW,
                    local_mixer=local_mixer[0],
                    mlp_ratio=mlp_ratio,
                    qkv_bias=qkv_bias,
                    qk_scale=qk_scale,
                    drop=drop_rate,
                    act_layer=act,
                    attn_drop=attn_drop_rate,
                    drop_path=dpr[0 : depth[0]][i],
                    norm_layer=norm_layer,
                    epsilon=epsilon,
                    prenorm=prenorm,
                )
                for i in range(depth[0])
            ]
        )
        if patch_merging is not None:
            self.sub_sample1 = SubSample(
                embed_dim[0],
                embed_dim[1],
                sub_norm=sub_norm,
                stride=[2, 1],
                types=patch_merging,
            )
            HW = [self.HW[0] // 2, self.HW[1]]
        else:
            HW = self.HW
        self.patch_merging = patch_merging
        self.blocks2 = nn.ModuleList(
            [
                Block_unit(
                    dim=embed_dim[1],
                    num_heads=num_heads[1],
                    mixer=mixer[depth[0] : depth[0] + depth[1]][i],
                    HW=HW,
                    local_mixer=local_mixer[1],
                    mlp_ratio=mlp_ratio,
                    qkv_bias=qkv_bias,
                    qk_scale=qk_scale,
                    drop=drop_rate,
                    act_layer=act,
                    attn_drop=attn_drop_rate,
                    drop_path=dpr[depth[0] : depth[0] + depth[1]][i],
                    norm_layer=norm_layer,
                    epsilon=epsilon,
                    prenorm=prenorm,
                )
                for i in range(depth[1])
            ]
        )
        if patch_merging is not None:
            self.sub_sample2 = SubSample(
                embed_dim[1],
                embed_dim[2],
                sub_norm=sub_norm,
                stride=[2, 1],
                types=patch_merging,
            )
            HW = [self.HW[0] // 4, self.HW[1]]
        else:
            HW = self.HW
        self.blocks3 = nn.ModuleList(
            [
                Block_unit(
                    dim=embed_dim[2],
                    num_heads=num_heads[2],
                    mixer=mixer[depth[0] + depth[1] :][i],
                    HW=HW,
                    local_mixer=local_mixer[2],
                    mlp_ratio=mlp_ratio,
                    qkv_bias=qkv_bias,
                    qk_scale=qk_scale,
                    drop=drop_rate,
                    act_layer=act,
                    attn_drop=attn_drop_rate,
                    drop_path=dpr[depth[0] + depth[1] :][i],
                    norm_layer=norm_layer,
                    epsilon=epsilon,
                    prenorm=prenorm,
                )
                for i in range(depth[2])
            ]
        )
        self.last_stage = last_stage
        if last_stage:
            self.avg_pool = nn.AdaptiveAvgPool2d([1, out_char_num])
            self.last_conv = nn.Conv2d(
                in_channels=embed_dim[2],
                out_channels=self.out_channels,
                kernel_size=1,
                stride=1,
                padding=0,
                bias=False,
            )
            self.hardswish = Activation("hard_swish", inplace=True)  # nn.Hardswish()
            # self.dropout = nn.Dropout(p=last_drop, mode="downscale_in_infer")
            self.dropout = nn.Dropout(p=last_drop)
        if not prenorm:
            self.norm = eval(norm_layer)(embed_dim[-1], eps=epsilon)
        self.use_lenhead = use_lenhead
        if use_lenhead:
            self.len_conv = nn.Linear(embed_dim[2], self.out_channels)
            self.hardswish_len = Activation(
                "hard_swish", inplace=True
            )  # nn.Hardswish()
            self.dropout_len = nn.Dropout(p=last_drop)

        torch.nn.init.xavier_normal_(self.pos_embed)
        self.apply(self._init_weights)