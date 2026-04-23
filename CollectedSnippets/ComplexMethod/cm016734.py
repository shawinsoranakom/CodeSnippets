def __init__(
        self,
        hidden_size: int,
        num_heads: int,
        mlp_ratio: float = 4.0,
        attn_mode: str = "xformers",
        qkv_bias: bool = False,
        pre_only: bool = False,
        rmsnorm: bool = False,
        scale_mod_only: bool = False,
        swiglu: bool = False,
        qk_norm: Optional[str] = None,
        x_block_self_attn: bool = False,
        dtype=None,
        device=None,
        operations=None,
        **block_kwargs,
    ):
        super().__init__()
        assert attn_mode in self.ATTENTION_MODES
        if not rmsnorm:
            self.norm1 = operations.LayerNorm(hidden_size, elementwise_affine=False, eps=1e-6, dtype=dtype, device=device)
        else:
            self.norm1 = RMSNorm(hidden_size, elementwise_affine=False, eps=1e-6)
        self.attn = SelfAttention(
            dim=hidden_size,
            num_heads=num_heads,
            qkv_bias=qkv_bias,
            attn_mode=attn_mode,
            pre_only=pre_only,
            qk_norm=qk_norm,
            rmsnorm=rmsnorm,
            dtype=dtype,
            device=device,
            operations=operations
        )
        if x_block_self_attn:
            assert not pre_only
            assert not scale_mod_only
            self.x_block_self_attn = True
            self.attn2 = SelfAttention(
                dim=hidden_size,
                num_heads=num_heads,
                qkv_bias=qkv_bias,
                attn_mode=attn_mode,
                pre_only=False,
                qk_norm=qk_norm,
                rmsnorm=rmsnorm,
                dtype=dtype,
                device=device,
                operations=operations
            )
        else:
            self.x_block_self_attn = False
        if not pre_only:
            if not rmsnorm:
                self.norm2 = operations.LayerNorm(
                    hidden_size, elementwise_affine=False, eps=1e-6, dtype=dtype, device=device
                )
            else:
                self.norm2 = RMSNorm(hidden_size, elementwise_affine=False, eps=1e-6)
        mlp_hidden_dim = int(hidden_size * mlp_ratio)
        if not pre_only:
            if not swiglu:
                self.mlp = Mlp(
                    in_features=hidden_size,
                    hidden_features=mlp_hidden_dim,
                    act_layer=lambda: nn.GELU(approximate="tanh"),
                    drop=0,
                    dtype=dtype,
                    device=device,
                    operations=operations
                )
            else:
                self.mlp = SwiGLUFeedForward(
                    dim=hidden_size,
                    hidden_dim=mlp_hidden_dim,
                    multiple_of=256,
                )
        self.scale_mod_only = scale_mod_only
        if x_block_self_attn:
            assert not pre_only
            assert not scale_mod_only
            n_mods = 9
        elif not scale_mod_only:
            n_mods = 6 if not pre_only else 2
        else:
            n_mods = 4 if not pre_only else 1
        self.adaLN_modulation = nn.Sequential(
            nn.SiLU(), operations.Linear(hidden_size, n_mods * hidden_size, bias=True, dtype=dtype, device=device)
        )
        self.pre_only = pre_only