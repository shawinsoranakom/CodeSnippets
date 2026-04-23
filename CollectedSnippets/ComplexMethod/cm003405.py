def __post_init__(self, **kwargs):
        if self.layer_types is None:
            # Default: linear attention for most layers, full attention every 4th layer
            self.layer_types = ["linear_attention"] * int(self.num_hidden_layers)
            for i in range(int(self.num_hidden_layers)):
                if i % 4 == 3:
                    self.layer_types[i] = "full_attention"
            # Ensure at least one full attention layer for small num_hidden_layers
            if "full_attention" not in self.layer_types:
                self.layer_types[-1] = "full_attention"

        if self.linear_num_key_heads is None:
            self.linear_num_key_heads = self.num_attention_heads
        if self.linear_num_value_heads is None:
            self.linear_num_value_heads = self.num_attention_heads
        if self.linear_key_head_dim is None:
            self.linear_key_head_dim = int(0.75 * self.hidden_size / self.linear_num_key_heads)
        if self.linear_value_head_dim is None:
            self.linear_value_head_dim = 2 * self.linear_key_head_dim
        if self.num_key_value_heads is None:
            self.num_key_value_heads = self.num_attention_heads

        super().__post_init__(**kwargs)