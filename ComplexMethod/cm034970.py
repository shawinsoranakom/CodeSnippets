def __init__(
        self,
        dim=64,
        out_dim=256,
        depth=3,
        mixer=["Local"] * 3,
        sub_k=[2, 1],
        num_heads=2,
        mlp_ratio=4,
        qkv_bias=True,
        qk_scale=None,
        drop_rate=0.0,
        attn_drop_rate=0.0,
        drop_path=[0.1] * 3,
        norm_layer=nn.LayerNorm,
        act=nn.GELU,
        eps=1e-6,
        downsample=None,
        **kwargs,
    ):
        super().__init__()
        self.dim = dim

        conv_block_num = sum([1 if mix == "Conv" else 0 for mix in mixer])
        blocks = []
        for i in range(depth):
            if mixer[i] == "Conv":
                blocks.append(
                    ConvBlock(
                        dim=dim,
                        num_heads=num_heads,
                        mlp_ratio=mlp_ratio,
                        drop=drop_rate,
                        act_layer=act,
                        drop_path=drop_path[i],
                        norm_layer=norm_layer,
                        epsilon=eps,
                    )
                )
            else:
                blocks.append(
                    Block(
                        dim=dim,
                        num_heads=num_heads,
                        mlp_ratio=mlp_ratio,
                        qkv_bias=qkv_bias,
                        qk_scale=qk_scale,
                        drop=drop_rate,
                        act_layer=act,
                        attn_drop=attn_drop_rate,
                        drop_path=drop_path[i],
                        norm_layer=norm_layer,
                        epsilon=eps,
                    )
                )
            if i == conv_block_num - 1 and mixer[-1] != "Conv":
                blocks.append(FlattenTranspose())
        self.blocks = nn.Sequential(*blocks)
        if downsample:
            if mixer[-1] == "Conv":
                self.downsample = SubSample2D(dim, out_dim, stride=sub_k)
            elif mixer[-1] == "Global":
                self.downsample = SubSample1D(dim, out_dim, stride=sub_k)
        else:
            self.downsample = IdentitySize()