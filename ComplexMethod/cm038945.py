def get_model_params(config):
    architectures = getattr(config, "architectures", None) or [type(config).__name__]
    architecture = architectures[0]

    if architecture == "DbrxForCausalLM":
        E = config.ffn_config.moe_num_experts
        topk = config.ffn_config.moe_top_k
        intermediate_size = config.ffn_config.ffn_hidden_size
        hidden_size = config.hidden_size
    elif architecture == "JambaForCausalLM":
        E = config.num_experts
        topk = config.num_experts_per_tok
        intermediate_size = config.intermediate_size
        hidden_size = config.hidden_size
    elif architecture in (
        "DeepseekV2ForCausalLM",
        "DeepseekV3ForCausalLM",
        "DeepseekV32ForCausalLM",
        "GlmMoeDsaForCausalLM",
        "Glm4MoeForCausalLM",
        "Glm4MoeLiteForCausalLM",
        "NemotronHForCausalLM",
        "MistralLarge3ForCausalLM",
    ):
        E = config.n_routed_experts
        topk = config.num_experts_per_tok
        intermediate_size = config.moe_intermediate_size
        hidden_size = config.hidden_size
    elif architecture in (
        "Qwen2MoeForCausalLM",
        "Qwen3MoeForCausalLM",
        "Qwen3NextForCausalLM",
    ):
        E = config.num_experts
        topk = config.num_experts_per_tok
        intermediate_size = config.moe_intermediate_size
        hidden_size = config.hidden_size
    elif architecture in (
        "Qwen3VLMoeForConditionalGeneration",
        "Qwen3_5MoeForConditionalGeneration",
        "Qwen3_5MoeTextConfig",
    ):
        text_config = config.get_text_config()
        E = text_config.num_experts
        topk = text_config.num_experts_per_tok
        intermediate_size = text_config.moe_intermediate_size
        hidden_size = text_config.hidden_size
    elif architecture == "HunYuanMoEV1ForCausalLM":
        E = config.num_experts
        topk = config.moe_topk[0]
        intermediate_size = config.moe_intermediate_size[0]
        hidden_size = config.hidden_size
    elif architecture == "Qwen3OmniMoeForConditionalGeneration":
        E = config.thinker_config.text_config.num_experts
        topk = config.thinker_config.text_config.num_experts_per_tok
        intermediate_size = config.thinker_config.text_config.moe_intermediate_size
        hidden_size = config.thinker_config.text_config.hidden_size
    elif architecture == "PixtralForConditionalGeneration":
        # Pixtral can contain different LLM architectures,
        # recurse to get their parameters
        return get_model_params(config.get_text_config())
    else:
        # Support for llama4
        config = config.get_text_config()
        # Default: Mixtral.
        E = config.num_local_experts
        topk = config.num_experts_per_tok
        intermediate_size = config.intermediate_size
        hidden_size = config.hidden_size
    return E, topk, intermediate_size, hidden_size