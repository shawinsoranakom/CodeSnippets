def forward(
        self,
        hidden_states: torch.FloatTensor,
        layer_past: Cache | None = None,
        attention_mask: torch.FloatTensor | None = None,
        position_ids: torch.LongTensor | None = None,
        use_cache: bool | None = False,
        output_attentions: bool | None = False,
        **kwargs,
    ) -> (
        tuple[torch.Tensor, tuple[torch.Tensor]]
        | tuple[torch.Tensor, tuple[torch.Tensor], tuple[torch.Tensor, ...]]
        | None
    ):
        query = self.q_proj(hidden_states)
        key = self.k_proj(hidden_states)
        value = self.v_proj(hidden_states)

        query = self._split_heads(query, self.num_attention_heads, self.head_dim, True)
        key = self._split_heads(key, self.num_attention_heads, self.head_dim, True)
        value = self._split_heads(value, self.num_attention_heads, self.head_dim, False)

        embed_positions = self._get_embed_positions(position_ids)

        repeated_position_ids = position_ids.unsqueeze(-1).repeat(1, 1, embed_positions.shape[-1])
        sincos = torch.gather(embed_positions, 1, repeated_position_ids).to(key.dtype)
        sin, cos = torch.split(sincos, sincos.shape[-1] // 2, dim=-1)

        if self.rotary_dim is not None:
            k_rot = key[:, :, :, : self.rotary_dim]
            k_pass = key[:, :, :, self.rotary_dim :]

            q_rot = query[:, :, :, : self.rotary_dim]
            q_pass = query[:, :, :, self.rotary_dim :]

            k_rot = apply_rotary_pos_emb(k_rot, sin, cos)
            q_rot = apply_rotary_pos_emb(q_rot, sin, cos)

            key = torch.cat([k_rot, k_pass], dim=-1)
            query = torch.cat([q_rot, q_pass], dim=-1)
        else:
            key = apply_rotary_pos_emb(key, sin, cos)
            query = apply_rotary_pos_emb(query, sin, cos)

        # tanspose to have the desired shape
        # before transpose: batch_size x seq_length x num_attention_heads x head_dim
        # after transpose: batch_size x num_attention_heads x seq_length x head_dim
        key = key.permute(0, 2, 1, 3)
        query = query.permute(0, 2, 1, 3)
        # value: batch_size x num_attention_heads x seq_length x head_dim

        if layer_past is not None:
            key, value = layer_past.update(key, value, self.layer_idx)

        # The Flash attention requires the input to have the shape
        # batch_size x seq_length x head_dim x hidden_dim
        # therefore we need to keep the original shape for query and key, and reshape value
        # to have the correct shape.
        key = key.permute(0, 2, 1, 3).contiguous()
        query = query.permute(0, 2, 1, 3).contiguous()
        value = value.permute(0, 2, 1, 3).contiguous()

        # In PEFT, usually we cast the layer norms in float32 for training stability reasons
        # therefore the input hidden states gets silently casted in float32. Hence, we need
        # cast them back in the correct dtype just to be sure everything works as expected.
        # This might slowdown training & inference so it is recommended to not cast the LayerNorms
        # in fp32. (LlamaRMSNorm handles it correctly)

        input_dtype = query.dtype
        device_type = query.device.type if query.device.type != "mps" else "cpu"
        if input_dtype == torch.float32:
            if torch.is_autocast_enabled(device_type):
                target_dtype = torch.get_autocast_dtype(device_type)
            # Handle the case where the model is quantized
            elif hasattr(self.config, "_is_quantized"):
                target_dtype = self.config.dtype
            else:
                target_dtype = self.q_proj.weight.dtype

            logger.warning_once(
                f"The input hidden states seems to be silently casted in float32, this might be related to"
                f" the fact you have upcasted embedding or layer norm layers in float32. We will cast back the input in"
                f" {target_dtype}."
            )

            query = query.to(target_dtype)
            key = key.to(target_dtype)
            value = value.to(target_dtype)

        attention_dropout = self.config.attn_pdrop if self.training else 0.0  # attn_pdrop in gptj

        query_length = query.shape[1]

        # Compute attention
        attn_weights = _flash_attention_forward(
            query,
            key,
            value,
            attention_mask,
            query_length,
            dropout=attention_dropout,
            is_causal=self.is_causal,
            use_top_left_mask=self._flash_attn_uses_top_left_mask,
        )

        # Reshape outputs
        attn_output = attn_weights.reshape(
            attn_weights.shape[0], attn_weights.shape[1], attn_weights.shape[2] * attn_weights.shape[3]
        )
        attn_output = self.out_proj(attn_output)
        attn_output = self.resid_dropout(attn_output)
        return attn_output, attn_weights