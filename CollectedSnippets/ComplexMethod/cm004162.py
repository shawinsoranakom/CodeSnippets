def __post_init__(self, **kwargs):
        if self.mlp_layer_types is None:
            self.mlp_layer_types = [
                "dense" if i < self.first_k_dense_replace else "sparse" for i in range(self.num_hidden_layers)
            ]
        if self.sliding_window is None:
            self.sliding_window_pattern = 0
        if self.layer_types is None:
            self.layer_types = [
                "sliding_attention"
                if ((i + 1) % (self.sliding_window_pattern) != 0 and i < self.num_hidden_layers)
                else "full_attention"
                for i in range(self.num_hidden_layers)
            ]

        super().__post_init__(**kwargs)