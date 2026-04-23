def extract_arch_config(hf_config) -> Optional[ModelArchConfig]:
    text_config = getattr(hf_config, "text_config", None) or hf_config

    hidden_size = getattr(text_config, "hidden_size", None)
    num_layers = getattr(text_config, "num_hidden_layers", None)
    num_heads = getattr(text_config, "num_attention_heads", None)
    intermediate_size = getattr(text_config, "intermediate_size", None)
    vocab_size = getattr(text_config, "vocab_size", None)

    if isinstance(intermediate_size, (list, tuple)):
        intermediate_size = intermediate_size[0] if intermediate_size else None
    if intermediate_size is None and hidden_size is not None:
        intermediate_size = hidden_size * 4

    if not all(
        v is not None
        for v in (hidden_size, num_layers, num_heads, intermediate_size, vocab_size)
    ):
        return None
    if num_heads <= 0:
        return None

    num_kv_heads = getattr(text_config, "num_key_value_heads", num_heads)

    num_experts = None
    for attr in ("num_local_experts", "num_experts", "n_routed_experts"):
        num_experts = getattr(text_config, attr, None)
        if num_experts is not None:
            break

    moe_intermediate = getattr(text_config, "moe_intermediate_size", None)
    n_shared_experts = getattr(text_config, "n_shared_experts", None) or 0

    num_dense_layers = 0
    if num_experts is not None and num_experts > 1:
        num_dense_layers = _compute_num_dense_layers(text_config, num_layers)

    q_lora_rank = getattr(text_config, "q_lora_rank", None)
    kv_lora_rank = getattr(text_config, "kv_lora_rank", None)
    qk_nope_head_dim = getattr(text_config, "qk_nope_head_dim", None)
    qk_rope_head_dim = getattr(text_config, "qk_rope_head_dim", None)
    v_head_dim = getattr(text_config, "v_head_dim", None)

    return ModelArchConfig(
        hidden_size = hidden_size,
        num_hidden_layers = num_layers,
        num_attention_heads = num_heads,
        num_key_value_heads = num_kv_heads,
        intermediate_size = intermediate_size,
        vocab_size = vocab_size,
        tie_word_embeddings = getattr(text_config, "tie_word_embeddings", True),
        num_experts = num_experts,
        moe_intermediate_size = moe_intermediate,
        n_shared_experts = n_shared_experts,
        num_dense_layers = num_dense_layers,
        q_lora_rank = q_lora_rank,
        kv_lora_rank = kv_lora_rank,
        qk_nope_head_dim = qk_nope_head_dim,
        qk_rope_head_dim = qk_rope_head_dim,
        v_head_dim = v_head_dim,
    )