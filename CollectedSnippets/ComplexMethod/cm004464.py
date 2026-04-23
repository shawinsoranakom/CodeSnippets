def __post_init__(self, **kwargs):
        if self.num_key_value_heads is None:
            self.num_key_value_heads = self.num_attention_heads

        if self.no_rope_layers is None:
            self.no_rope_layers = [
                int((layer_idx + 1) % self.no_rope_layer_interval != 0) for layer_idx in range(self.num_hidden_layers)
            ]

        if self.layer_types is None:
            self.layer_types = []
            for layer_idx in range(self.num_hidden_layers):
                has_rope = self.no_rope_layers[layer_idx]
                if self.use_sliding_window and self.sliding_window is not None and not has_rope:
                    self.layer_types.append("sliding_attention")
                else:
                    self.layer_types.append("full_attention")

        super().__post_init__(**kwargs)