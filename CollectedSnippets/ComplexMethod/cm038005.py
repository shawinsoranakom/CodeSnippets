def layer_fn(prefix):
            layer_idx = int(prefix.split(".")[-1])
            layer_config = config
            layer_config.attention_type = self.decoder_attention_types[layer_idx]
            layer_config.layer_idx = layer_idx

            decoder_kwargs = {
                "quant_config": quant_config,
                "layer_id": layer_idx,
                "model_config": model_config,
                "cache_config": cache_config,
            }

            if layer_config.attention_type == 0:
                decoder_kwargs["linear_layer_id"] = sum(
                    1 for i in range(layer_idx) if self.decoder_attention_types[i] == 0
                )
            else:
                decoder_kwargs["linear_layer_id"] = None

            if hasattr(config, "num_local_experts") and isinstance(
                config.num_local_experts, list
            ):
                decoder_kwargs["expert_num"] = config.num_local_experts[layer_idx]
            elif hasattr(config, "num_local_experts") and isinstance(
                config.num_local_experts, int
            ):
                decoder_kwargs["expert_num"] = config.num_local_experts
            else:
                decoder_kwargs["expert_num"] = 1

            return MiniMaxText01DecoderLayer(
                layer_config, **decoder_kwargs, prefix=prefix
            )