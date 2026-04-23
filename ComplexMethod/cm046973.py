def LlamaModel_fast_forward_inference_custom(
        self,
        input_ids,
        past_key_values,
        position_ids,
        attention_mask = None,
        **kwargs,
    ):
        input_ids = input_ids[:, : self.max_seq_length]
        bsz, q_len = input_ids.shape
        hd = self.config.hidden_size
        mlp_size = self.config.intermediate_size

        X = self.model.embed_tokens(input_ids)
        X = X.to(_get_dtype(dtype_from_config(self.config)))
        bsz, q_len, hd = X.shape
        assert q_len == 1
        # Get saved buffers to reduce memory movement
        residual = torch.empty(
            (bsz, q_len, hd), dtype = torch.float32, device = f"{DEVICE_TYPE_TORCH}:0"
        )
        _XX = torch.empty(
            (2, bsz, q_len, hd), dtype = torch.float32, device = f"{DEVICE_TYPE_TORCH}:0"
        )
        XX, XX2 = _XX[0], _XX[1]
        variance = torch.empty(
            (bsz, q_len, 1), dtype = torch.float32, device = f"{DEVICE_TYPE_TORCH}:0"
        )
        temp_mlp = torch.empty(
            (2, bsz, 1, mlp_size), dtype = X.dtype, device = f"{DEVICE_TYPE_TORCH}:0"
        )
        temp_gates, temp_ups = (
            tuple(temp_mlp[0].to(torch.device(x)) for x in range(DEVICE_COUNT)),
            tuple(temp_mlp[1].to(torch.device(x)) for x in range(DEVICE_COUNT)),
        )

        seq_len = past_key_values[0][0].shape[-2]
        kv_seq_len = seq_len + 1
        if attention_mask is not None:
            attention_mask = _prepare_4d_causal_attention_mask_for_sdpa(
                attention_mask,
                (bsz, q_len),
                X,
                seq_len,
                sliding_window = getattr(self.config, "sliding_window", None),
            )
            # Pre-convert to bool once for all layers (avoids per-layer .eq(0))
            if attention_mask is not None and attention_mask.dtype != torch.bool:
                attention_mask = attention_mask.eq(0)
        else:
            attention_mask = None

        # Compute rotary_seq_len once to avoid per-layer GPU-CPU sync from .item()
        rotary_seq_len = max(kv_seq_len, int(position_ids.max().item()) + 1)

        next_decoder_cache = []

        for idx, decoder_layer in enumerate(self.model.layers):
            device_index = getattr(decoder_layer, "_per_layer_device_index", 0)
            X, residual, position_ids = move_to_device(
                device_index, X, residual, position_ids
            )
            residual.copy_(X)  # residual = X
            X = fast_rms_layernorm_inference(
                decoder_layer.input_layernorm,
                X,
                XX = XX,
                XX2 = XX2,
                variance = variance,
            )
            X, present_key_value = attention_fast_forward_inference(
                decoder_layer.self_attn,
                hidden_states = X,
                past_key_value = past_key_values[idx],
                position_ids = position_ids,
                attention_mask = attention_mask,
                do_prefill = not hasattr(decoder_layer.self_attn, "paged_attention"),
                rotary_seq_len = rotary_seq_len,
            )
            X += residual

            residual.copy_(X)  # residual = X
            X = fast_rms_layernorm_inference(
                decoder_layer.post_attention_layernorm,
                X,
                XX = XX,
                XX2 = XX2,
                variance = variance,
            )
            X = mlp_fast_forward_inference(
                decoder_layer.mlp,
                X,
                temp_gate = temp_gates[device_index],
                temp_up = temp_ups[device_index],
            )
            X += residual

            next_decoder_cache.append(present_key_value)
        X = fast_rms_layernorm_inference(
            self.model.norm,
            X,
            XX = XX,
            XX2 = XX2,
            variance = variance,
        )

        return BaseModelOutputWithPast(
            last_hidden_state = X,
            past_key_values = next_decoder_cache,
            hidden_states = [],
            attentions = [],
        )