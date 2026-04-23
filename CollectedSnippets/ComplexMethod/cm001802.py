def update_config_headdim(config, requested_dim):
            # Flex Attention cannot use dropout
            if hasattr(config, "attention_dropout"):
                config.attention_dropout = 0.0
            if hasattr(config, "attention_probs_dropout_prob"):
                config.attention_probs_dropout_prob = 0.0

            # Update the head dim and try to update hidden size as well if present in config
            # NOTE: some models may have none if the values in sub-config, thus we check for `Noneness`
            head_dim = None
            if hasattr(config, "head_dim") and config.head_dim is not None:
                head_dim = config.head_dim
                config.head_dim = max(requested_dim, config.head_dim)

            cross_head_dim = None
            if hasattr(config, "cross_head_dim") and config.cross_head_dim is not None:
                cross_head_dim = config.cross_head_dim
                config.cross_head_dim = max(requested_dim, config.cross_head_dim)

            if (
                getattr(config, "hidden_size", None) is not None
                and getattr(config, "num_attention_heads", None) is not None
            ):
                # For some models, num_attention_heads is a list of ints: we take the max to maximize the multiplier
                num_attn_heads = getattr(config, "num_attention_heads")
                num_attn_heads = num_attn_heads if isinstance(num_attn_heads, int) else max(num_attn_heads)
                head_dim = head_dim if head_dim is not None else config.hidden_size // num_attn_heads
                config.hidden_size *= max(requested_dim // head_dim, 1)

            if (
                getattr(config, "decoder_hidden_size", None) is not None
                and getattr(config, "decoder_num_attention_heads", None) is not None
            ):
                decoder_head_dim = config.decoder_hidden_size // config.decoder_num_attention_heads
                config.decoder_hidden_size *= max(requested_dim // decoder_head_dim, 1)

            if (
                getattr(config, "cross_hidden_size", None) is not None
                and getattr(config, "cross_num_attention_heads", None) is not None
            ):
                cross_head_dim = (
                    cross_head_dim
                    if cross_head_dim is not None
                    else config.cross_hidden_size // config.cross_num_attention_heads
                )
                config.cross_hidden_size *= max(requested_dim // cross_head_dim, 1)

            # 3d rope also depends on the head dim
            # (we assume easy shapes here where we get to the requested head dim at least)
            if (
                getattr(config, "rope_parameters", None) is not None
                and len(config.rope_parameters.get("mrope_section", [])) > 0
            ):
                scaling_factor = max(requested_dim // (sum(config.rope_parameters["mrope_section"]) * 2), 1)
                config.rope_parameters["mrope_section"] = [
                    section * scaling_factor for section in config.rope_parameters["mrope_section"]
                ]