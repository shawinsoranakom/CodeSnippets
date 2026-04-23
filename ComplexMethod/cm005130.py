def convert_transformer_weights(
    config: Gemma3TextConfig,
    paths: Sequence[str],
    weights: np.ndarray,
) -> Iterator[tuple[str, np.ndarray]]:
    path, prop = paths

    if path.startswith(_TRANSFORMER_POST_TRAINING_PREFIX):
        path = path[_TRANSFORMER_POST_TRAINING_PREFIX_LEN:]

    converted_paths: list[str] = []
    converted_weights: list[Any] = []

    attn_head_dim = config.num_attention_heads * config.head_dim
    kv_head_dim = config.num_key_value_heads * config.head_dim

    if path.endswith(_TRANSFORMER_EMBEDDER):
        if prop == "input_embedding":
            # Tied to language_model.lm_head.weight, assigned at the end.
            converted_paths = ["model.language_model.embed_tokens.weight"]

            if _INCLUDE_VISION_ENCODER.value:
                # Gemma3 model doesn't have image soft token in input and output embeddings, resize to avoid bugs we had with Mllama
                pre_expansion_embeddings = weights
                mu = np.mean(pre_expansion_embeddings, axis=0)
                sigma = np.cov(pre_expansion_embeddings, rowvar=False, bias=True)
                new_embeddings = np.random.multivariate_normal(mu, 1e-5 * sigma, size=64)
                weights = np.vstack([pre_expansion_embeddings, new_embeddings])
                config.vocab_size += 64

            converted_weights = [weights]
        elif not _INCLUDE_VISION_ENCODER.value or prop in ("mm_output_embedding", "mm_input_embedding_extra"):
            return zip([], [])
        else:
            raise ValueError(f"Unexpected member, {prop}, in Embedder.")
    elif f"{_TRANSFORMER_EMBEDDER}/mm_" in path:
        if not _INCLUDE_VISION_ENCODER.value:
            return zip([], [])

        if path.endswith("/mm_input_projection"):
            converted_paths = ["model.multi_modal_projector.mm_input_projection_weight"]
            converted_weights = [weights]
        elif path.endswith("/mm_soft_embedding_norm"):
            converted_paths = ["model.multi_modal_projector.mm_soft_emb_norm.weight"]
            converted_weights = [weights]
        else:
            raise ValueError(f"Unexpected subpath, `{path}`, in Embedder.")
    elif path.endswith(_TRANSFORMER_FINAL_NORM):
        converted_paths = ["model.language_model.norm.weight"]
        converted_weights = [weights]
    elif _TRANSFORMER_DECODER_BLOCK in path:
        decoder_block_start = path.find(_TRANSFORMER_DECODER_BLOCK)
        decoder_block_offset = decoder_block_start + _TRANSFORMER_DECODER_BLOCK_LEN
        decoder_block_path = path[decoder_block_offset:]
        next_path_separator_idx = decoder_block_path.find("/")
        layer_idx = decoder_block_path[:next_path_separator_idx]
        decoder_block_path = decoder_block_path[next_path_separator_idx:]

        base_path = f"model.language_model.layers.{layer_idx}"

        if path.endswith("attn/attn_vec_einsum"):
            converted_paths = [f"{base_path}.self_attn.o_proj.weight"]
            converted_weights = [weights.transpose(2, 0, 1).reshape(config.hidden_size, attn_head_dim)]
        elif path.endswith("attn/_key_norm"):
            converted_paths = [f"{base_path}.self_attn.k_norm.weight"]
            converted_weights = [weights]
        elif path.endswith("attn/kv_einsum"):
            converted_paths = [
                f"{base_path}.self_attn.k_proj.weight",
                f"{base_path}.self_attn.v_proj.weight",
            ]
            k_proj_weights, v_proj_weights = weights
            converted_weights = [
                k_proj_weights.transpose(0, 2, 1).reshape(kv_head_dim, config.hidden_size),
                v_proj_weights.transpose(0, 2, 1).reshape(kv_head_dim, config.hidden_size),
            ]
        elif path.endswith("attn/q_einsum"):
            converted_paths = [f"{base_path}.self_attn.q_proj.weight"]
            converted_weights = [weights.transpose(0, 2, 1).reshape(attn_head_dim, config.hidden_size)]
        elif path.endswith("attn/_query_norm"):
            converted_paths = [f"{base_path}.self_attn.q_norm.weight"]
            converted_weights = [weights]
        elif path.endswith("mlp/gating_einsum"):
            converted_paths = [
                f"{base_path}.mlp.gate_proj.weight",
                f"{base_path}.mlp.up_proj.weight",
            ]
            gate_proj_weight, up_proj_weight = weights
            converted_weights = [gate_proj_weight, up_proj_weight]
        elif path.endswith("mlp/linear"):
            converted_paths = [f"{base_path}.mlp.down_proj.weight"]
            converted_weights = [weights.transpose()]
        elif path.endswith("post_attention_norm"):
            converted_paths = [f"{base_path}.post_attention_layernorm.weight"]
            converted_weights = [weights]
        elif path.endswith("post_ffw_norm"):
            converted_paths = [f"{base_path}.post_feedforward_layernorm.weight"]
            converted_weights = [weights]
        elif path.endswith("pre_attention_norm"):
            converted_paths = [f"{base_path}.input_layernorm.weight"]
            converted_weights = [weights]
        elif path.endswith("pre_ffw_norm"):
            converted_paths = [f"{base_path}.pre_feedforward_layernorm.weight"]
            converted_weights = [weights]
        else:
            raise ValueError(f"Unexpected path `{path}` in Decoder Block.")

    if (cpl := len(converted_paths)) != (cwl := len(converted_weights)):
        raise ValueError(
            "The `converted_paths` and `converted_weights` should be the same "
            f"length. Got {cpl} and {cwl}, respectively, for {path}."
        )

    return zip(converted_paths, converted_weights)