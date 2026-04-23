def __init__(self, config):
        super().__init__()

        self.layer = nn.ModuleList([DebertaV2Layer(config) for _ in range(config.num_hidden_layers)])
        self.relative_attention = getattr(config, "relative_attention", False)

        if self.relative_attention:
            self.max_relative_positions = getattr(config, "max_relative_positions", -1)
            if self.max_relative_positions < 1:
                self.max_relative_positions = config.max_position_embeddings

            self.position_buckets = getattr(config, "position_buckets", -1)
            pos_ebd_size = self.max_relative_positions * 2

            if self.position_buckets > 0:
                pos_ebd_size = self.position_buckets * 2

            self.rel_embeddings = nn.Embedding(pos_ebd_size, config.hidden_size)

        self.norm_rel_ebd = [x.strip() for x in getattr(config, "norm_rel_ebd", "none").lower().split("|")]

        if "layer_norm" in self.norm_rel_ebd:
            self.LayerNorm = LayerNorm(config.hidden_size, config.layer_norm_eps, elementwise_affine=True)

        self.conv = ConvLayer(config) if getattr(config, "conv_kernel_size", 0) > 0 else None
        self.gradient_checkpointing = False