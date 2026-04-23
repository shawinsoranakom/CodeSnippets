def __post_init__(self, **kwargs):
        self.mlp_only_layers = [] if self.mlp_only_layers is None else self.mlp_only_layers
        self.sliding_window = self.sliding_window if self.use_sliding_window else 0
        if self.layer_types is None:
            self.layer_types = [
                "sliding_attention"
                if bool((i + 1) % 2) and i < self.max_window_layers and self.use_sliding_window
                else "full_attention"
                for i in range(self.num_hidden_layers)
            ]

        super().__post_init__(**kwargs)