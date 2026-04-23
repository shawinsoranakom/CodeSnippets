def __init__(self, config: OlmoHybridConfig):
        super().__init__()
        self.layer_types = config.layer_types
        self.transformer_layers = [
            i for i in range(config.num_hidden_layers) if self.layer_types[i] == "full_attention"
        ]
        self.last_linear_layer = len(self.layer_types) - 1 - self.layer_types[::-1].index("linear_attention")
        self.recurrent_states = [None for _ in range(config.num_hidden_layers)]
        self.key_cache = [None for _ in range(config.num_hidden_layers)]
        self.value_cache = [None for _ in range(config.num_hidden_layers)]
        # Replace single conv_states with separate q, k, v conv states
        self.conv_states_q = [None for _ in range(config.num_hidden_layers)]
        self.conv_states_k = [None for _ in range(config.num_hidden_layers)]
        self.conv_states_v = [None for _ in range(config.num_hidden_layers)]