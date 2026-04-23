def create_attention_instances(self) -> dict[int, Attention]:
        """
        Create `Attention` instances to inform KV cache allocation.
        """
        text_config = self.text_config

        num_heads = self.model_config.get_num_attention_heads(self.parallel_config)
        head_size = self.model_config.get_head_size()
        num_kv_heads = self.model_config.get_num_kv_heads(self.parallel_config)
        logits_soft_cap = getattr(text_config, "attn_logit_softcapping", None)

        # In encoder models, the attention layers will have `is_causal=False`
        is_encoder = lambda module: not getattr(module, "is_causal", True)
        has_encoder = lambda model: any(is_encoder(m) for m in model.modules())
        is_multimodal = lambda config: config != config.get_text_config()
        # vLLM does not support encoder-decoder models, so if any encoder layer is
        # found in a text only model, we assume the whole model is an encoder model
        if has_encoder(self.model) and not is_multimodal(self.config):
            self.check_version("5.0.0", "encoder models support")
            attn_type = AttentionType.ENCODER_ONLY
        else:
            attn_type = AttentionType.DECODER

        pp_rank = self.pp_group.rank_in_group
        pp_size = self.pp_group.world_size
        start, end = get_pp_indices(text_config.num_hidden_layers, pp_rank, pp_size)

        attention_instances = {}
        for i in range(start, end):
            # Handle interleaved sliding window attention
            per_layer_sliding_window = None
            if (
                hasattr(self.config, "layer_types")
                and self.config.layer_types[i] == "sliding_attention"
            ):
                per_layer_sliding_window = self.config.sliding_window

            attn_cls = (
                EncoderOnlyAttention
                if attn_type == AttentionType.ENCODER_ONLY
                else Attention
            )
            attention_instances[i] = attn_cls(
                num_heads=num_heads,
                head_size=head_size,
                # NOTE: We use Llama scale as default, if it's set by
                # Transformers, it's updated in vllm_flash_attention_forward
                scale=head_size**-0.5,
                num_kv_heads=num_kv_heads,
                cache_config=self.cache_config,
                quant_config=self.quant_config,
                logits_soft_cap=logits_soft_cap,
                per_layer_sliding_window=per_layer_sliding_window,
                prefix=f"{i}.attn",
                attn_type=attn_type,
            )
        return attention_instances