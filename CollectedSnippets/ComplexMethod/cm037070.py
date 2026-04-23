def __init__(
        self,
        vocab_size=256000,
        hidden_size=6144,
        intermediate_size=24576,
        num_hidden_layers=32,
        num_attention_heads=48,
        head_dim=None,
        num_key_value_heads=None,
        hidden_act="relu2",
        max_position_embeddings=4096,
        initializer_range=0.0134,
        norm_eps=1e-5,
        use_cache=True,
        pad_token_id=None,
        bos_token_id=2,
        eos_token_id=3,
        tie_word_embeddings=False,
        rope_parameters=None,
        attention_bias=False,
        attention_dropout=0.0,
        mlp_bias=False,
        **kwargs,
    ):
        self.vocab_size = vocab_size
        self.max_position_embeddings = max_position_embeddings
        self.hidden_size = hidden_size
        self.intermediate_size = intermediate_size
        self.num_hidden_layers = num_hidden_layers
        self.num_attention_heads = num_attention_heads
        head_dim = head_dim or kwargs.get("kv_channels")
        self.head_dim = (
            head_dim if head_dim is not None else (hidden_size // num_attention_heads)
        )

        # for backward compatibility
        if num_key_value_heads is None:
            num_key_value_heads = num_attention_heads

        self.num_key_value_heads = num_key_value_heads
        self.hidden_act = hidden_act
        self.initializer_range = initializer_range
        self.norm_eps = norm_eps
        self.use_cache = use_cache
        # Try to set `rope_scaling` if available, otherwise use `rope_parameters`
        rope_scaling = kwargs.pop("rope_scaling", None)
        rope_parameters = rope_scaling or rope_parameters or {"rope_type": "default"}
        rope_theta = kwargs.pop("rope_theta", 10000.0)
        if "rope_theta" not in rope_parameters:
            rope_parameters["rope_theta"] = rope_theta
        # for backward compatibility
        partial_rotary_factor = (
            kwargs.get("rope_percent")
            or kwargs.get("rope_percentage")
            or kwargs.get("partial_rotary_factor")
            or 0.5
        )
        if "partial_rotary_factor" not in rope_parameters:
            rope_parameters["partial_rotary_factor"] = partial_rotary_factor
        self.rope_parameters = rope_parameters
        self._rope_parameters_validation()
        self.attention_bias = attention_bias
        self.attention_dropout = attention_dropout
        self.mlp_bias = mlp_bias

        super().__init__(
            pad_token_id=pad_token_id,
            bos_token_id=bos_token_id,
            eos_token_id=eos_token_id,
            tie_word_embeddings=tie_word_embeddings,
            **kwargs,
        )