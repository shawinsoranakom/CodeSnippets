def __init__(
        self,
        vocab_size=131072,
        hidden_size=4096,
        intermediate_size=8192,
        num_layers=28,
        num_hidden_layers=None,
        num_attention_heads=96,
        num_key_value_heads=128,
        ep_size=1,
        kv_lora_rank=512,
        q_lora_rank=1536,
        qk_rope_head_dim=64,
        v_head_dim=128,
        qk_nope_head_dim=128,
        num_experts_per_tok=None,
        norm_topk_prob=False,
        max_position_embeddings=8192,
        initializer_range=0.02,
        rms_norm_eps=1e-05,
        use_cache=True,
        pad_token_id=None,
        bos_token_id=100000,
        eos_token_id=100001,
        pretraining_tp=1,
        tie_word_embeddings=False,
        rope_parameters=None,
        attention_bias=False,
        attention_dropout=0.0,
        mla_scale_q_lora=False,
        mla_scale_kv_lora=False,
        dtype="bfloat16",
        params_dtype="bfloat16",
        router_dtype="float32",
        router_bias=False,
        topk_method=None,
        routed_scaling_factor=1.0,
        zero_expert_num=0,
        zero_expert_type=None,
        nextn_use_scmoe=False,
        **kwargs,
    ):
        super().__init__(
            pad_token_id=pad_token_id,
            bos_token_id=bos_token_id,
            eos_token_id=eos_token_id,
            tie_word_embeddings=tie_word_embeddings,
            dtype=dtype,
            params_dtype=params_dtype,
            router_dtype=router_dtype,
            topk_method=topk_method,
            router_bias=router_bias,
            nextn_use_scmoe=nextn_use_scmoe,
            **kwargs,
        )
        self.vocab_size = vocab_size
        self.max_position_embeddings = max_position_embeddings
        self.hidden_size = hidden_size
        self.num_hidden_layers = (
            num_hidden_layers if num_hidden_layers is not None else num_layers
        )
        self.num_attention_heads = num_attention_heads
        self.ep_size = ep_size
        self.kv_lora_rank = kv_lora_rank
        self.q_lora_rank = q_lora_rank
        self.qk_rope_head_dim = qk_rope_head_dim
        self.v_head_dim = v_head_dim
        self.qk_nope_head_dim = qk_nope_head_dim
        self.num_experts_per_tok = num_experts_per_tok
        self.norm_topk_prob = norm_topk_prob
        # for backward compatibility
        if num_key_value_heads is None:
            num_key_value_heads = num_attention_heads

        self.num_key_value_heads = num_key_value_heads
        self.initializer_range = initializer_range
        self.rms_norm_eps = rms_norm_eps
        self.pretraining_tp = pretraining_tp
        self.use_cache = use_cache
        # Try to set `rope_scaling` if available, otherwise use `rope_parameters`
        rope_scaling = kwargs.pop("rope_scaling", None)
        rope_parameters = rope_scaling or rope_parameters or {"rope_type": "default"}
        rope_theta = kwargs.pop("rope_theta", 1000000.0)
        if "rope_theta" not in rope_parameters:
            rope_parameters["rope_theta"] = rope_theta
        self.rope_parameters = rope_parameters
        self.attention_bias = attention_bias
        self.attention_dropout = attention_dropout
        self.mla_scale_q_lora = mla_scale_q_lora
        self.mla_scale_kv_lora = mla_scale_kv_lora
        self.zero_expert_num = zero_expert_num
        self.zero_expert_type = zero_expert_type
        self.routed_scaling_factor = routed_scaling_factor
        self.hidden_act = "silu"
        self.intermediate_size = (
            self.ffn_hidden_size
            if hasattr(self, "ffn_hidden_size")
            else intermediate_size
        )
        if hasattr(self, "moe_intermediate_size"):
            self.moe_intermediate_size = self.moe_intermediate_size
        elif hasattr(self, "expert_ffn_hidden_size"):
            self.moe_intermediate_size = self.expert_ffn_hidden_size
        else:
            self.moe_intermediate_size = self.intermediate_size