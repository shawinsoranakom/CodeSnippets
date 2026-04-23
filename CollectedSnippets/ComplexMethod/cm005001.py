def convert_ssm_config_to_hf_config(
    config_ssm: dict,
    **kwargs,
) -> BambaConfig:
    """Convert a config from mamba_ssm to a BambaConfig from here."""
    hf_config: BambaConfig = BambaConfig(**kwargs)

    hf_config.architectures = ["BambaForCausalLM"]

    # Set important values from config and recalculate other resulting entries
    hf_config.hidden_size = config_ssm["d_model"]
    hf_config.intermediate_size = config_ssm["d_intermediate"]
    hf_config.mamba_n_heads = (hf_config.hidden_size * hf_config.mamba_expand) // hf_config.mamba_d_head
    hf_config.num_hidden_layers = config_ssm["n_layer"]
    hf_config.tie_word_embeddings = config_ssm["tie_embeddings"]

    # currently this script assumes config_ssm belongs to v2
    if config_ssm["ssm_cfg"].get("layer") != "Mamba2":
        raise ValueError("Conversion script only supports Mamba2")

    # Set attention values
    attn_cfg = config_ssm.get("attn_cfg")
    if attn_cfg:
        assert attn_cfg["causal"], "Only support non-causal attention."
        assert not attn_cfg["qkv_proj_bias"], "Only support no qkv bias."
        assert not attn_cfg["out_proj_bias"], "Only support no out bias."
        hf_config.attn_rotary_emb = attn_cfg["rotary_emb_dim"]
        hf_config.num_attention_heads = attn_cfg["num_heads"]
        hf_config.num_key_value_heads = attn_cfg["num_heads_kv"]

    attention_layer_indices = config_ssm.get("attn_layer_idx")
    if attention_layer_indices:
        hf_config.attn_layer_indices = attention_layer_indices

    # Padded vocab size, mostly of 16 but 32 is also very common in different models
    vocab_size = config_ssm["vocab_size"]
    pad_vocab_size_multiple = config_ssm["pad_vocab_size_multiple"]
    if (vocab_size % pad_vocab_size_multiple) != 0:
        vocab_size += pad_vocab_size_multiple - (vocab_size % pad_vocab_size_multiple)
    hf_config.vocab_size = vocab_size

    return hf_config