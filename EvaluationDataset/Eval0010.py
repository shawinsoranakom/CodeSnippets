class DuplicatedMethodConfig(PreTrainedConfig):
    model_type = "duplicated_method"
    keys_to_ignore_at_inference = ["past_key_values"]
    base_model_tp_plan = {
        "layers.*.self_attn.q_proj": "colwise",
        "layers.*.self_attn.k_proj": "colwise",
        "layers.*.self_attn.v_proj": "colwise",
        "layers.*.self_attn.o_proj": "rowwise",
        "layers.*.mlp.gate_proj": "colwise",
        "layers.*.mlp.up_proj": "colwise",
        "layers.*.mlp.down_proj": "rowwise",
    }
    base_model_pp_plan = {
        "embed_tokens": (["input_ids"], ["inputs_embeds"]),
        "layers": (["hidden_states", "attention_mask"], ["hidden_states"]),
        "norm": (["hidden_states"], ["hidden_states"]),
    }

    def __init__(
        self,
        vocab_size: Optional[int] = 32000,
        hidden_size: Optional[int] = 4096,
        intermediate_size: Optional[int] = 11008,
        num_hidden_layers: Optional[int] = 32,
        num_attention_heads: Optional[int] = 32,
        num_key_value_heads: Optional[int] = None,
        hidden_act: Optional[str] = "silu",
        max_position_embeddings: Optional[int] = 2048,
        initializer_range: Optional[float] = 0.02,
        rms_norm_eps: Optional[int] = 1e-6,
        use_cache: Optional[bool] = True,
        pad_token_id: Optional[int] = None,
        bos_token_id: Optional[int] = 1,
        eos_token_id: Optional[int] = 2,
        pretraining_tp: Optional[int] = 1,
        tie_word_embeddings: Optional[bool] = False,
        rope_parameters: Optional[RopeParameters | dict[RopeParameters]] = None,
        attention_bias: Optional[bool] = False,
        attention_dropout: Optional[float] = 0.0,
        mlp_bias: Optional[bool] = False,
        head_dim: Optional[int] = None,
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
        self.attention_bias = attention_bias
        self.attention_dropout = attention_dropout
        self.mlp_bias = mlp_bias
        self.head_dim = head_dim if head_dim is not None else self.hidden_size // self.num_attention_heads
        # Try to set `rope_scaling` if available, otherwise use `rope_parameters`
        rope_scaling = kwargs.pop("rope_scaling", None)
        self.rope_parameters = rope_scaling or rope_parameters

        rope_theta = kwargs.get("rope_theta", 10000.0)
        standardize_rope_params(self, rope_theta=rope_theta)
        rope_config_validation(self)

        super().__init__(
            pad_token_id=pad_token_id,
            bos_token_id=bos_token_id,
            eos_token_id=eos_token_id,
            tie_word_embeddings=tie_word_embeddings,
            **kwargs,
        )

    @property
    def vocab_size(self):
        return 45

    @vocab_size.setter
    def vocab_size(self, value):
        self.vocab_size = value
