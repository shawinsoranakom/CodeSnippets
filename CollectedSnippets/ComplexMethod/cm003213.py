def forward(
        self,
        hidden_states: torch.Tensor,
        alibi: torch.Tensor | None,
        attention_mask: torch.Tensor,
        position_ids: torch.LongTensor | None = None,
        layer_past: Cache | None = None,
        use_cache: bool = False,
        output_attentions: bool = False,
        position_embeddings: tuple[torch.Tensor, torch.Tensor] | None = None,
        **kwargs,
    ):
        fused_qkv = self.query_key_value(hidden_states)  # [batch_size, seq_length, 3 x hidden_size]
        num_kv_heads = self.num_heads if self.new_decoder_architecture else self.num_kv_heads
        # 3 x [batch_size, seq_length, num_heads, head_dim]
        (query_layer, key_layer, value_layer) = self._split_heads(fused_qkv)

        batch_size, query_length, _, _ = query_layer.shape

        query_layer = query_layer.transpose(1, 2).reshape(batch_size, self.num_heads, query_length, self.head_dim)
        key_layer = key_layer.transpose(1, 2).reshape(batch_size, num_kv_heads, query_length, self.head_dim)
        value_layer = value_layer.transpose(1, 2).reshape(batch_size, num_kv_heads, query_length, self.head_dim)

        if alibi is None:
            cos, sin = position_embeddings
            query_layer, key_layer = apply_rotary_pos_emb(query_layer, key_layer, cos, sin)

        if layer_past is not None:
            key_layer, value_layer = layer_past.update(key_layer, value_layer, self.layer_idx)

        # TODO: These transpose are quite inefficient but Flash Attention requires the layout [batch_size, sequence_length, num_heads, head_dim]. We would need to refactor the KV cache
        # to be able to avoid many of these transpose/reshape/view.
        query_layer = query_layer.transpose(1, 2)
        key_layer = key_layer.transpose(1, 2)
        value_layer = value_layer.transpose(1, 2)

        if alibi is not None:
            raise ValueError("`alibi` is not supported when `use_flash_attn` is True")

        attn_dropout = self.config.attention_dropout if self.training else 0.0

        # In PEFT, usually we cast the layer norms in float32 for training stability reasons
        # therefore the input hidden states gets silently casted in float32. Hence, we need
        # cast them back in float16 just to be sure everything works as expected.
        input_dtype = query_layer.dtype
        device_type = query_layer.device.type if query_layer.device.type != "mps" else "cpu"
        if input_dtype == torch.float32:
            if torch.is_autocast_enabled(device_type):
                target_dtype = torch.get_autocast_dtype(device_type)
            # Handle the case where the model is quantized
            elif hasattr(self.config, "_is_quantized"):
                target_dtype = self.config.dtype
            else:
                target_dtype = self.query_key_value.weight.dtype

            logger.warning_once(
                f"The input hidden states seems to be silently casted in float32, this might be related to"
                f" the fact you have upcasted embedding or layer norm layers in float32. We will cast back the input in"
                f" {target_dtype}."
            )

            query_layer = query_layer.to(target_dtype)
            key_layer = key_layer.to(target_dtype)
            value_layer = value_layer.to(target_dtype)

        attn_output = _flash_attention_forward(
            query_layer,
            key_layer,
            value_layer,
            attention_mask,
            query_length,
            position_ids=position_ids,
            dropout=attn_dropout,
            is_causal=self.is_causal,
            use_top_left_mask=self._flash_attn_uses_top_left_mask,
        )

        attn_weights = attn_output.reshape(batch_size, query_length, self.num_heads * self.head_dim)
        attn_output = self.dense(attn_weights)

        if not output_attentions:
            attn_weights = None

        return attn_output, attn_weights