def __post_init__(self, **kwargs):
        if self.num_key_value_heads is None:
            self.num_key_value_heads = self.num_attention_heads

        default_no_rope_layers = [
            int((layer_idx + 1) % self.no_rope_layer_interval != 0) for layer_idx in range(self.num_hidden_layers)
        ]
        self.no_rope_layers = self.no_rope_layers if self.no_rope_layers else default_no_rope_layers
        self.head_dim = self.head_dim if self.head_dim is not None else self.hidden_size // self.num_attention_heads

        self.moe_layers = (
            self.moe_layers
            if self.moe_layers is not None
            else list(
                range(
                    self.interleave_moe_layer_step - 1,
                    self.num_hidden_layers,
                    self.interleave_moe_layer_step,
                )
            )
        )

        if self.layer_types is None:
            self.layer_types = [
                "chunked_attention" if no_rope else "full_attention" for no_rope in self.no_rope_layers
            ]

        super().__post_init__(**kwargs)