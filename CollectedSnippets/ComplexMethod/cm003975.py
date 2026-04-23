def __init__(self, config: Gemma4TextConfig, layer_idx: int):
        super().__init__()
        self.layer_type = config.layer_types[layer_idx] if hasattr(config, "layer_types") else None
        self.config = config
        self.layer_idx = layer_idx
        self.is_sliding = self.layer_type == "sliding_attention"
        self.sliding_window = config.sliding_window if self.is_sliding else None

        self.head_dim = config.global_head_dim if not self.is_sliding and config.global_head_dim else config.head_dim
        self.use_alternative_attention = config.attention_k_eq_v and not self.is_sliding
        num_key_value_heads = (
            config.num_global_key_value_heads if self.use_alternative_attention else config.num_key_value_heads
        )
        self.num_key_value_groups = config.num_attention_heads // num_key_value_heads
        self.scaling = 1.0
        self.attention_dropout = self.config.attention_dropout
        self.is_causal = config.use_bidirectional_attention != "all"

        # Shared kv cache
        first_kv_shared_layer_idx = self.config.num_hidden_layers - getattr(self.config, "num_kv_shared_layers", 0)
        self.is_kv_shared_layer = layer_idx >= first_kv_shared_layer_idx > 0
        prev_layers = config.layer_types[:first_kv_shared_layer_idx]
        if self.is_kv_shared_layer:
            # For shared layers, find the last non-shared layer of the same type before sharing starts
            self.kv_shared_layer_index = len(prev_layers) - 1 - prev_layers[::-1].index(config.layer_types[layer_idx])
            self.store_full_length_kv = False
        else:
            self.kv_shared_layer_index = None
            # For non-shared layers, store full-length kv if this is the last non-shared layer of its type
            self.store_full_length_kv = layer_idx == len(prev_layers) - 1 - prev_layers[::-1].index(
                config.layer_types[layer_idx]
            )

        self.q_proj = nn.Linear(
            config.hidden_size, config.num_attention_heads * self.head_dim, bias=config.attention_bias
        )
        self.q_norm = Gemma4RMSNorm(dim=self.head_dim, eps=config.rms_norm_eps)

        # Layers sharing kv states don't need any weight matrices
        if not self.is_kv_shared_layer:
            self.k_norm = Gemma4RMSNorm(dim=self.head_dim, eps=config.rms_norm_eps)
            self.v_norm = Gemma4RMSNorm(self.head_dim, eps=config.rms_norm_eps, with_scale=False)

            self.k_proj = nn.Linear(
                config.hidden_size, num_key_value_heads * self.head_dim, bias=config.attention_bias
            )
            self.v_proj = (
                nn.Linear(config.hidden_size, num_key_value_heads * self.head_dim, bias=config.attention_bias)
                if not self.use_alternative_attention
                else None
            )

        self.o_proj = nn.Linear(
            config.num_attention_heads * self.head_dim, config.hidden_size, bias=config.attention_bias
        )