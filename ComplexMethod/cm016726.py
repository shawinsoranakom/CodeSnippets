def __init__(self, dim, n_heads, d_head, dropout=0., context_dim=None, gated_ff=True, checkpoint=True, ff_in=False, inner_dim=None,
                 disable_self_attn=False, disable_temporal_crossattention=False, switch_temporal_ca_to_sa=False, attn_precision=None, dtype=None, device=None, operations=ops):
        super().__init__()

        self.ff_in = ff_in or inner_dim is not None
        if inner_dim is None:
            inner_dim = dim

        self.is_res = inner_dim == dim
        self.attn_precision = attn_precision

        if self.ff_in:
            self.norm_in = operations.LayerNorm(dim, dtype=dtype, device=device)
            self.ff_in = FeedForward(dim, dim_out=inner_dim, dropout=dropout, glu=gated_ff, dtype=dtype, device=device, operations=operations)

        self.disable_self_attn = disable_self_attn
        self.attn1 = CrossAttention(query_dim=inner_dim, heads=n_heads, dim_head=d_head, dropout=dropout,
                              context_dim=context_dim if self.disable_self_attn else None, attn_precision=self.attn_precision, dtype=dtype, device=device, operations=operations)  # is a self-attention if not self.disable_self_attn
        self.ff = FeedForward(inner_dim, dim_out=dim, dropout=dropout, glu=gated_ff, dtype=dtype, device=device, operations=operations)

        if disable_temporal_crossattention:
            if switch_temporal_ca_to_sa:
                raise ValueError
            else:
                self.attn2 = None
        else:
            context_dim_attn2 = None
            if not switch_temporal_ca_to_sa:
                context_dim_attn2 = context_dim

            self.attn2 = CrossAttention(query_dim=inner_dim, context_dim=context_dim_attn2,
                                heads=n_heads, dim_head=d_head, dropout=dropout, attn_precision=self.attn_precision, dtype=dtype, device=device, operations=operations)  # is self-attn if context is none
            self.norm2 = operations.LayerNorm(inner_dim, dtype=dtype, device=device)

        self.norm1 = operations.LayerNorm(inner_dim, dtype=dtype, device=device)
        self.norm3 = operations.LayerNorm(inner_dim, dtype=dtype, device=device)
        self.n_heads = n_heads
        self.d_head = d_head
        self.switch_temporal_ca_to_sa = switch_temporal_ca_to_sa