def __init__(self, *, vllm_config: VllmConfig, prefix: str = ""):
        super().__init__()
        config: MiniMaxConfig = vllm_config.model_config.hf_config
        model_config = vllm_config.model_config
        quant_config = vllm_config.quant_config
        cache_config = vllm_config.cache_config
        scheduler_config = vllm_config.scheduler_config
        self.config = config
        self.CONCAT_FFN = True

        self.vocab_size = config.vocab_size

        self.decoder_attention_types = getattr(
            config, "attn_type_list", False
        ) or getattr(config, "decoder_attention_types", False)
        # The HF format uses "layer_types" instead of "attn_type_list"
        # where "linear_attention" is 0 and "full_attention" is 1
        if not self.decoder_attention_types and hasattr(config, "layer_types"):
            self.decoder_attention_types = []
            for layer_type in config.layer_types:
                if layer_type == "linear_attention":
                    self.decoder_attention_types.append(0)
                elif layer_type == "full_attention":
                    self.decoder_attention_types.append(1)
                else:
                    raise ValueError(f"Unsupported layer type: {layer_type}")
        # Default to full attention
        if not self.decoder_attention_types:
            self.decoder_attention_types = [1] * config.num_hidden_layers
        self.num_layers = config.num_hidden_layers

        self._layer_barrier = False
        if get_pp_group().is_first_rank:
            self.embed_tokens = VocabParallelEmbedding(
                self.vocab_size,
                config.hidden_size,
                org_num_embeddings=self.vocab_size,
            )
        else:
            self.embed_tokens = PPMissingLayer()

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

        self.start_layer, self.end_layer, self.layers = make_layers(
            config.num_hidden_layers, layer_fn, prefix=f"{prefix}.layers"
        )

        linear_layer_nums = sum(
            1
            for i in range(config.num_hidden_layers)
            if self.decoder_attention_types[i] == 0
        )
        max_slots_number = scheduler_config.max_num_seqs
        self.cache_shape = (
            linear_layer_nums,
            max_slots_number,
            config.num_attention_heads // get_tensor_model_parallel_world_size(),
            config.head_dim,
            config.head_dim,
        )
        _dummy = torch.zeros(1)
        self._dtype = _dummy.dtype
        del _dummy

        norm_kwargs = {}
        if hasattr(config, "rms_norm_eps"):
            norm_kwargs["eps"] = config.rms_norm_eps
        if get_pp_group().is_last_rank:
            self.norm = RMSNorm(config.hidden_size, **norm_kwargs)
        else:
            self.norm = PPMissingLayer()
        self.embed_scale = 1.0
        return