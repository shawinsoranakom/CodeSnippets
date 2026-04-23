def __init__(
        self,
        *,
        num_tokens,
        max_seq_len,
        attn_layers,
        emb_dim=None,
        max_mem_len=0.0,
        emb_dropout=0.0,
        num_memory_tokens=None,
        tie_embedding=False,
        use_pos_emb=True,
        is_export=False,
    ):
        super().__init__()
        assert isinstance(
            attn_layers, AttentionLayers
        ), "attention layers must be one of Encoder or Decoder"

        dim = attn_layers.dim
        emb_dim = default(emb_dim, dim)

        self.max_seq_len = max_seq_len
        self.max_mem_len = max_mem_len

        self.token_emb = nn.Embedding(num_tokens, emb_dim)
        self.pos_emb = (
            AbsolutePositionalEmbedding(emb_dim, max_seq_len)
            if (use_pos_emb and not attn_layers.has_pos_emb)
            else always(0)
        )
        self.emb_dropout = nn.Dropout(emb_dropout)

        self.project_emb = nn.Linear(emb_dim, dim) if emb_dim != dim else nn.Identity()
        self.attn_layers = attn_layers
        self.norm = nn.LayerNorm(dim)
        self.is_export = is_export

        self.init_()

        self.to_logits = (
            nn.Linear(dim, num_tokens)
            if not tie_embedding
            else lambda t: t @ self.token_emb.weight.t()
        )

        # memory tokens (like [cls]) from Memory Transformers paper
        num_memory_tokens = default(num_memory_tokens, 0)
        self.num_memory_tokens = num_memory_tokens
        if num_memory_tokens > 0:
            self.memory_tokens = create_latex_parameter([num_memory_tokens, dim])

            # let funnel encoder know number of memory tokens, if specified
            # TODO: think of a cleaner solution
            if hasattr(attn_layers, "num_memory_tokens"):
                attn_layers.num_memory_tokens = num_memory_tokens