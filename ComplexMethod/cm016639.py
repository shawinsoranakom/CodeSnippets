def __init__(
        self,
        query_dim: int,
        cross_attention_dim: Optional[int] = None,
        heads: int = 8,
        kv_heads: Optional[int] = None,
        dim_head: int = 64,
        dropout: float = 0.0,
        bias: bool = False,
        qk_norm: Optional[str] = None,
        added_kv_proj_dim: Optional[int] = None,
        added_proj_bias: Optional[bool] = True,
        out_bias: bool = True,
        scale_qk: bool = True,
        only_cross_attention: bool = False,
        eps: float = 1e-5,
        rescale_output_factor: float = 1.0,
        residual_connection: bool = False,
        processor=None,
        out_dim: int = None,
        out_context_dim: int = None,
        context_pre_only=None,
        pre_only=False,
        elementwise_affine: bool = True,
        is_causal: bool = False,
        dtype=None, device=None, operations=None
    ):
        super().__init__()

        self.inner_dim = out_dim if out_dim is not None else dim_head * heads
        self.inner_kv_dim = self.inner_dim if kv_heads is None else dim_head * kv_heads
        self.query_dim = query_dim
        self.use_bias = bias
        self.is_cross_attention = cross_attention_dim is not None
        self.cross_attention_dim = cross_attention_dim if cross_attention_dim is not None else query_dim
        self.rescale_output_factor = rescale_output_factor
        self.residual_connection = residual_connection
        self.dropout = dropout
        self.fused_projections = False
        self.out_dim = out_dim if out_dim is not None else query_dim
        self.out_context_dim = out_context_dim if out_context_dim is not None else query_dim
        self.context_pre_only = context_pre_only
        self.pre_only = pre_only
        self.is_causal = is_causal

        self.scale_qk = scale_qk
        self.scale = dim_head**-0.5 if self.scale_qk else 1.0

        self.heads = out_dim // dim_head if out_dim is not None else heads
        # for slice_size > 0 the attention score computation
        # is split across the batch axis to save memory
        # You can set slice_size with `set_attention_slice`
        self.sliceable_head_dim = heads

        self.added_kv_proj_dim = added_kv_proj_dim
        self.only_cross_attention = only_cross_attention

        if self.added_kv_proj_dim is None and self.only_cross_attention:
            raise ValueError(
                "`only_cross_attention` can only be set to True if `added_kv_proj_dim` is not None. Make sure to set either `only_cross_attention=False` or define `added_kv_proj_dim`."
            )

        self.group_norm = None
        self.spatial_norm = None

        self.norm_q = None
        self.norm_k = None

        self.norm_cross = None
        self.to_q = operations.Linear(query_dim, self.inner_dim, bias=bias, dtype=dtype, device=device)

        if not self.only_cross_attention:
            # only relevant for the `AddedKVProcessor` classes
            self.to_k = operations.Linear(self.cross_attention_dim, self.inner_kv_dim, bias=bias, dtype=dtype, device=device)
            self.to_v = operations.Linear(self.cross_attention_dim, self.inner_kv_dim, bias=bias, dtype=dtype, device=device)
        else:
            self.to_k = None
            self.to_v = None

        self.added_proj_bias = added_proj_bias
        if self.added_kv_proj_dim is not None:
            self.add_k_proj = operations.Linear(added_kv_proj_dim, self.inner_kv_dim, bias=added_proj_bias, dtype=dtype, device=device)
            self.add_v_proj = operations.Linear(added_kv_proj_dim, self.inner_kv_dim, bias=added_proj_bias, dtype=dtype, device=device)
            if self.context_pre_only is not None:
                self.add_q_proj = operations.Linear(added_kv_proj_dim, self.inner_dim, bias=added_proj_bias, dtype=dtype, device=device)
        else:
            self.add_q_proj = None
            self.add_k_proj = None
            self.add_v_proj = None

        if not self.pre_only:
            self.to_out = nn.ModuleList([])
            self.to_out.append(operations.Linear(self.inner_dim, self.out_dim, bias=out_bias, dtype=dtype, device=device))
            self.to_out.append(nn.Dropout(dropout))
        else:
            self.to_out = None

        if self.context_pre_only is not None and not self.context_pre_only:
            self.to_add_out = operations.Linear(self.inner_dim, self.out_context_dim, bias=out_bias, dtype=dtype, device=device)
        else:
            self.to_add_out = None

        self.norm_added_q = None
        self.norm_added_k = None
        self.processor = processor