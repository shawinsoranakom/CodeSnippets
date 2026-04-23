def __init__(
        self,
        vocab_size=32000,
        hidden_size=4096,
        intermediate_size=11008,
        num_hidden_layers=32,
        num_attention_heads=32,
        num_key_value_heads=None,
        hidden_act="silu",
        max_position_embeddings=2048,
        initializer_range=0.02,
        rms_norm_eps=1e-6,
        use_cache=True,
        pad_token_id=None,
        bos_token_id=1,
        eos_token_id=2,
        pretraining_tp=1,
        tie_word_embeddings=False,
        rope_theta=10000.0,
        rope_scaling=None,
        attention_bias=False,
        attention_dropout=0.0,
        mlp_bias=False,
        head_dim=None,
        embedding_multiplier=None,  # mup
        logits_scaling=None,  # mup
        attention_multiplier=None,  # mup
        residual_multiplier=None,  # mup
        use_post_norm=True,  # post-norm(peri-LN)
        rope_parameters=None,
        auto_map=None,
        **kwargs,
    ):
        self.vocab_size = vocab_size
        self.max_position_embeddings = max_position_embeddings
        self.hidden_size = hidden_size
        self.intermediate_size = intermediate_size
        self.num_hidden_layers = num_hidden_layers
        self.num_attention_heads = num_attention_heads

        # for backward compatibility
        if num_key_value_heads is None:
            num_key_value_heads = num_attention_heads

        self.num_key_value_heads = num_key_value_heads
        self.hidden_act = hidden_act
        self.initializer_range = initializer_range
        self.rms_norm_eps = rms_norm_eps
        self.pretraining_tp = pretraining_tp
        self.use_cache = use_cache
        self.rope_theta = rope_theta
        self.rope_scaling = rope_scaling
        self.attention_bias = attention_bias
        self.attention_dropout = attention_dropout
        self.mlp_bias = mlp_bias
        self.head_dim = (
            head_dim
            if head_dim is not None
            else self.hidden_size // self.num_attention_heads
        )
        # Derive rope_parameters for vLLM's get_rope() from rope_theta /
        # rope_scaling, unless the caller already provided rope_parameters.
        if rope_parameters is None:
            if rope_scaling is not None:
                # Shallow-copy to avoid mutating the caller's dict.
                rope_parameters = dict(rope_scaling)
                # BC: 'type' field -> 'rope_type', remove stale key.
                if "type" in rope_parameters:
                    rope_parameters.setdefault("rope_type", rope_parameters.pop("type"))
            else:
                rope_parameters = {"rope_type": "default"}
            if "rope_theta" not in rope_parameters:
                rope_parameters["rope_theta"] = rope_theta
        self.rope_parameters = rope_parameters

        # BC: keep self.rope_scaling consistent for HF serialization.
        if self.rope_scaling is not None and "type" in self.rope_scaling:
            self.rope_scaling["rope_type"] = self.rope_scaling["type"]

        # mup
        self.embedding_multiplier = (
            embedding_multiplier if embedding_multiplier is not None else 1.0
        )
        self.logits_scaling = logits_scaling if logits_scaling is not None else 1.0
        self.attention_multiplier = (
            attention_multiplier
            if attention_multiplier is not None
            else self.head_dim**-0.5
        )
        self.residual_multiplier = (
            residual_multiplier if residual_multiplier is not None else 1.0
        )

        # post-norm (Peri-LN)
        self.use_post_norm = use_post_norm

        super().__init__(
            pad_token_id=pad_token_id,
            bos_token_id=bos_token_id,
            eos_token_id=eos_token_id,
            tie_word_embeddings=tie_word_embeddings,
            auto_map=auto_map,
            **kwargs,
        )