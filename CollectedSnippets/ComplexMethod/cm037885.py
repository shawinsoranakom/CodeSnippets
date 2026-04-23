def verify_and_update_model_config(model_config: "ModelConfig") -> None:
        config = model_config.hf_config

        assert config.__class__.__name__ == "NomicBertConfig"
        assert config.activation_function in ["swiglu", "gelu"]
        config.position_embedding_type = getattr(
            config, "position_embedding_type", "rope"
        )

        if config.activation_function == "swiglu":
            config.hidden_act = "silu"
        else:
            config.hidden_act = config.activation_function

        assert config.mlp_fc1_bias == config.mlp_fc2_bias == config.qkv_proj_bias
        config.bias = config.qkv_proj_bias

        assert config.rotary_emb_scale_base is None
        assert not config.rotary_emb_interleaved

        config.layer_norm_eps = config.layer_norm_epsilon
        config.intermediate_size = config.n_inner
        config.hidden_size = config.n_embd
        config.num_hidden_layers = config.n_layer
        model_config.model_arch_config.hidden_size = config.hidden_size
        model_config.model_arch_config.total_num_hidden_layers = (
            config.num_hidden_layers
        )

        head_dim = config.hidden_size // config.num_attention_heads
        max_trained_positions = getattr(config, "max_trained_positions", 2048)

        config.rotary_kwargs = {
            "head_size": head_dim,
            "max_position": max_trained_positions,
            "rope_parameters": config.rope_parameters,
        }

        # we ignore config.rotary_scaling_factor so that for datasets shorter
        # than max_trained_positions 2048, the results are consistent
        # with SentenceTransformer.
        # The context extension uses vllm style rope_theta and rope_parameters.
        # See #17785 #18755
        if (
            not model_config.hf_overrides
            and model_config.original_max_model_len is None
        ):
            # Default
            # Reset max_model_len to max_trained_positions.
            # nomic-embed-text-v2-moe the length is set to 512
            # by sentence_bert_config.json.
            max_model_len_before = model_config.max_model_len
            max_model_len = min(model_config.max_model_len, max_trained_positions)

            model_config.max_model_len = model_config.get_and_verify_max_len(
                max_model_len
            )

            if model_config.max_model_len != max_model_len_before:
                logger.warning(
                    "Nomic context extension is disabled. "
                    "Changing max_model_len from %s to %s. "
                    "To enable context extension, see: "
                    "https://github.com/vllm-project/vllm/tree/main/examples/offline_inference/context_extension.py",
                    max_model_len_before,
                    model_config.max_model_len,
                )
        else:
            # We need to re-verify max_model_len to avoid lengths
            # greater than position_embedding.
            hf_text_config = model_config.hf_text_config

            if isinstance(model_config.hf_overrides, dict):
                # hf_overrides_kw
                max_model_len = model_config.hf_overrides.get(
                    "max_model_len", model_config.max_model_len
                )
            else:
                # hf_overrides_fn
                # This might be overridden by sentence_bert_config.json.
                max_model_len = model_config.max_model_len

            # reset hf_text_config for recalculate_max_model_len.
            if hasattr(hf_text_config, "max_model_len"):
                delattr(hf_text_config, "max_model_len")
            hf_text_config.max_position_embeddings = max_trained_positions
            hf_text_config.rope_parameters = config.rotary_kwargs["rope_parameters"]

            # Update the cached derived_max_model_len to enforce the limit
            model_config.model_arch_config.derived_max_model_len_and_key = (
                float(max_trained_positions),
                "max_position_embeddings",
            )

            # The priority of sentence_bert_config.json is higher
            # than max_position_embeddings
            encoder_config = deepcopy(model_config.encoder_config)
            encoder_config.pop("max_seq_length", None)
            model_config.encoder_config = encoder_config

            model_config.max_model_len = model_config.get_and_verify_max_len(
                max_model_len
            )