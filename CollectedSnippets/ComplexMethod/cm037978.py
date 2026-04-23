def maybe_update_quant_config(
        self, quant_config: QuantizationConfig
    ) -> QuantizationConfig:
        """
        Update quant config to so that ignored module and target module names
        match the vLLM model names.
        Right now this is specific for compressed-tensors format and
        load_format mistral.
        """
        remapping_rules = [
            (r"output", r"language_model.lm_head"),
            (
                r"layers\.(\d+)\.attention\.wo",
                r"language_model.model.layers.\1.self_attn.out_proj",
            ),
            (
                r"layers\.(\d+)\.attention\.w(.*)",
                r"language_model.model.layers.\1.self_attn.\2_proj",
            ),
            (
                r"layers\.(\d+)\.feed_forward\.w1",
                r"language_model.model.layers.\1.mlp.gate_proj",
            ),
            (
                r"layers\.(\d+)\.feed_forward\.w2",
                r"language_model.model.layers.\1.mlp.down_proj",
            ),
            (
                r"layers\.(\d+)\.feed_forward\.w3",
                r"language_model.model.layers.\1.mlp.up_proj",
            ),
            (
                r"mm_whisper_embeddings\.whisper_encoder\.transformer\.layers\.(\d+)\.attention.w(.*)",
                r"whisper_encoder.whisper_encoder.layers.\1.layers.self_attn.\2_proj",
            ),
            (
                r"mm_whisper_embeddings\.whisper_encoder\.transformer\.layers\.(\d+)\.attention.wo",
                r"whisper_encoder.whisper_encoder.layers.\1.layers.self_attn.out_proj",
            ),
            (
                r"mm_whisper_embeddings\.whisper_encoder\.transformer\.layers\.(\d+)\.feed_forward.w(\d+)",
                r"whisper_encoder.whisper_encoder.layers.\1.layers.mlp.fc\2",
            ),
            (
                r"mm_whisper_embeddings\.whisper_encoder\.conv_layers\.0",
                r"whisper_encoder.whisper_encoder.conv1",
            ),
            (
                r"mm_whisper_embeddings\.whisper_encoder\.conv_layers\.1",
                r"whisper_encoder.whisper_encoder.conv2",
            ),
            (
                r"mm_whisper_embeddings\.audio_language_projection\.0",
                r"audio_language_adapter.w_in",
            ),
            (
                r"mm_whisper_embeddings\.audio_language_projection\.2",
                r"audio_language_adapter.w_out",
            ),
        ]

        # Update ignore list
        if hasattr(quant_config, "ignore"):
            mistral_ignore = []
            for name in quant_config.ignore:
                mistral_name = name
                for pattern, repl in remapping_rules:
                    if re.fullmatch(pattern, name):
                        mistral_name = re.sub(pattern, repl, name)
                mistral_ignore.append(mistral_name)
            quant_config.ignore = mistral_ignore

        # Update target list
        if hasattr(quant_config, "config_groups"):
            config_groups = quant_config.config_groups
            for group_name in config_groups:
                if "targets" in config_groups[group_name]:
                    targets = []
                    for name in config_groups[group_name]["targets"]:
                        mistral_name = name
                        for pattern, repl in remapping_rules:
                            if re.fullmatch(pattern, name):
                                mistral_name = re.sub(pattern, repl, name)
                        targets.append(mistral_name)
                config_groups[group_name]["targets"] = targets
            quant_config.config_groups = config_groups

        return quant_config