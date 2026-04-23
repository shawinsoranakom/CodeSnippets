def __init__(
        self,
        vocab_size: int | None = 100352,
        hidden_size: int | None = 3840,
        intermediate_size: int | None = 11008,
        num_hidden_layers: int | None = 32,
        num_attention_heads: int | None = 30,
        num_key_value_heads: int | None = None,
        hidden_act: str | None = "silu",
        max_position_embeddings: int | None = 65536,
        initializer_range: float | None = 0.02,
        use_cache: bool | None = True,
        pad_token_id: int | None = 100277,
        bos_token_id: int | None = None,
        eos_token_id: int | None = 100257,
        tie_word_embeddings: bool | None = False,
        rope_parameters=None,
        attention_bias: bool | None = False,
        attention_dropout: float | None = 0.0,
        rms_norm_eps: float | None = 1e-06,
        layer_types: list[str] | None = None,
        linear_num_key_heads: int | None = None,
        linear_num_value_heads: int | None = None,
        linear_key_head_dim: int | None = None,
        linear_value_head_dim: int | None = None,
        linear_a_log_min: float = 0.0,
        linear_a_log_max: float = 16.0,
        linear_dt_min: float = 0.001,
        linear_dt_max: float = 0.1,
        linear_dt_init_floor: float = 1e-4,
        linear_conv_kernel_dim: int = 4,
        linear_allow_neg_eigval: bool = True,
        **kwargs,
    ):
        super().__init__(**kwargs)

        assert num_hidden_layers is not None
        assert hidden_size is not None
        assert num_attention_heads is not None

        if layer_types is None:
            # Default: linear attention for most layers, full attention every 4th layer
            layer_types = ["linear_attention"] * int(num_hidden_layers)
            for i in range(int(num_hidden_layers)):
                if i % 4 == 3:
                    layer_types[i] = "full_attention"
            # Ensure at least one full attention layer for small num_hidden_layers
            if "full_attention" not in layer_types:
                layer_types[-1] = "full_attention"

        if hasattr(self, "validate_layer_type"):
            # Transformers v5
            self.layer_types = layer_types
            self.validate_layer_type()
        else:
            # Transformers v4
            from transformers.configuration_utils import layer_type_validation

            layer_type_validation(layer_types, num_hidden_layers)
        if "linear_attention" not in layer_types:
            raise ValueError(
                "OLMoHybrid expects at least one 'linear_attention' layer."
            )
        if all(t == "linear_attention" for t in layer_types):
            raise ValueError("OLMoHybrid expects at least one attention layer.")

        self.layer_types = layer_types

        if linear_num_key_heads is None:
            linear_num_key_heads = num_attention_heads
        if linear_num_value_heads is None:
            linear_num_value_heads = num_attention_heads
        if linear_key_head_dim is None:
            linear_key_head_dim = int(0.75 * hidden_size / linear_num_key_heads)
        if linear_value_head_dim is None:
            linear_value_head_dim = 2 * linear_key_head_dim

        self.linear_num_key_heads = linear_num_key_heads
        self.linear_num_value_heads = linear_num_value_heads
        self.linear_key_head_dim = linear_key_head_dim
        self.linear_value_head_dim = linear_value_head_dim
        self.linear_a_log_min = linear_a_log_min
        self.linear_a_log_max = linear_a_log_max
        self.linear_dt_min = linear_dt_min
        self.linear_dt_max = linear_dt_max
        self.linear_dt_init_floor = linear_dt_init_floor
        self.linear_conv_kernel_dim = linear_conv_kernel_dim
        self.linear_allow_neg_eigval = linear_allow_neg_eigval
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
        self.use_cache = use_cache
        self.attention_bias = attention_bias
        self.attention_dropout = attention_dropout
        self.rope_parameters = rope_parameters

        self.tie_word_embeddings = tie_word_embeddings
        self.pad_token_id = pad_token_id
        self.bos_token_id = bos_token_id
        self.eos_token_id = eos_token_id