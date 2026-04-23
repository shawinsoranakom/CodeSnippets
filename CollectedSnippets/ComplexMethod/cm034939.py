def __init__(
        self,
        embed_dim,
        num_heads,
        dropout=0.0,
        bias=True,
        add_bias_kv=False,
        add_zero_attn=False,
        kdim=None,
        vdim=None,
        batch_first=False,
        device=None,
        dtype=None,
        is_export=False,
    ) -> None:
        super(MyMultiheadAttention, self).__init__()
        self.embed_dim = embed_dim
        self.kdim = kdim if kdim is not None else embed_dim
        self.vdim = vdim if vdim is not None else embed_dim
        self._qkv_same_embed_dim = self.kdim == embed_dim and self.vdim == embed_dim

        self.num_heads = num_heads
        self.dropout = dropout
        self.batch_first = batch_first
        self.head_dim = embed_dim // num_heads
        self.is_export = is_export
        assert (
            self.head_dim * num_heads == self.embed_dim
        ), "embed_dim must be divisible by num_heads"

        if self._qkv_same_embed_dim is False:
            pass
        else:
            if dtype is None:
                dtype = paddle.float32
            self.in_proj_weight = paddle.create_parameter(
                (3 * embed_dim, embed_dim), dtype
            )
            self.q_proj_weight = None
            self.k_proj_weight = None
            self.v_proj_weight = None

        if bias:
            self.in_proj_bias = paddle.create_parameter((3 * embed_dim,), dtype)
            zeros_(self.in_proj_bias)
        else:
            self.in_proj_bias = None
        self.out_proj = nn.Linear(embed_dim, embed_dim, bias_attr=bias)

        if add_bias_kv:
            pass
        else:
            self.bias_k = self.bias_v = None

        self.add_zero_attn = add_zero_attn

        self._reset_parameters()