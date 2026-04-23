def __post_init__(self, **kwargs):
        if self.rope_parameters is None:
            self.rope_parameters = {
                "rope_theta": 1_000_000.0,
                "factor": 16.0,
                "high_freq_factor": 4.0,
                "low_freq_factor": 1.0,
                "original_max_position_embeddings": 8192,
                "rope_type": "llama3",
            }

        if self.layer_types is None:
            # Default pattern: every 4th layer uses full attention, others use sliding attention
            window_pattern = 4
            self.layer_types = [
                ("full_attention" if (i % window_pattern == 0) else "sliding_attention")
                for i in range(self.num_hidden_layers)
            ]

        self.sliding_window = int(self.sliding_window) if self.sliding_window else None
        self.layer_types = list(self.layer_types)
        self.eos_token_id = self.eos_token_id if self.eos_token_id is not None else [128001, 128008, 128009]
        if self.head_dim is None:
            self.head_dim = self.hidden_size // self.num_attention_heads
        if self.num_key_value_heads is None:
            self.num_key_value_heads = self.num_attention_heads

        super().__post_init__(**kwargs)