def llama_flash_attention_2_forward(
    self: "LlamaFlashAttention2",
    hidden_states: "torch.Tensor",
    attention_mask: Optional["torch.Tensor"] = None,
    position_ids: Optional["torch.LongTensor"] = None,
    past_key_value: Optional["Cache"] = None,
    output_attentions: bool = False,
    cache_position: Optional["torch.LongTensor"] = None,
    position_embeddings: Optional[tuple["torch.Tensor", "torch.Tensor"]] = None,
    **kwargs,
) -> tuple["torch.Tensor", Optional["torch.Tensor"], Optional[tuple["torch.Tensor"]]]:
    # LlamaFlashAttention2 attention does not support output_attentions
    output_attentions = False

    bsz, q_len, _ = hidden_states.size()

    query_states: torch.Tensor = self.q_proj(hidden_states)
    key_states: torch.Tensor = self.k_proj(hidden_states)
    value_states: torch.Tensor = self.v_proj(hidden_states)

    query_states = query_states.view(bsz, q_len, self.num_heads, self.head_dim).transpose(1, 2)
    key_states = key_states.view(bsz, q_len, self.num_key_value_heads, self.head_dim).transpose(1, 2)
    value_states = value_states.view(bsz, q_len, self.num_key_value_heads, self.head_dim).transpose(1, 2)

    if position_embeddings is None:
        cos, sin = self.rotary_emb(value_states, position_ids)
    else:
        cos, sin = position_embeddings

    query_states, key_states = apply_rotary_pos_emb(query_states, key_states, cos, sin)

    if past_key_value is not None:
        cache_kwargs = {"sin": sin, "cos": cos, "cache_position": cache_position}
        key_states, value_states = past_key_value.update(key_states, value_states, self.layer_idx, cache_kwargs)

    key_states = repeat_kv(key_states, self.num_key_value_groups)
    value_states = repeat_kv(value_states, self.num_key_value_groups)

    # FlashAttention requires the input to have the shape (bsz, seq_len, n_heads, head_dim)
    query_states = query_states.transpose(1, 2)
    key_states = key_states.transpose(1, 2)
    value_states = value_states.transpose(1, 2)

    dropout_rate = self.attention_dropout if self.training else 0.0

    input_dtype = query_states.dtype
    if input_dtype == torch.float32:
        if torch.is_autocast_enabled():
            target_dtype = torch.get_autocast_gpu_dtype()
        elif hasattr(self.config, "_pre_quantization_dtype"):
            target_dtype = self.config._pre_quantization_dtype
        else:
            target_dtype = self.q_proj.weight.dtype

        transformers_logger.warning_once("The input hidden states seems to be silently casted in float32.")
        query_states = query_states.to(target_dtype)
        key_states = key_states.to(target_dtype)
        value_states = value_states.to(target_dtype)

    if getattr(self.config, "group_size_ratio", None) and self.training:  # shift
        groupsz = int(q_len * getattr(self.config, "group_size_ratio"))
        assert q_len % groupsz == 0, f"q_len {q_len} should be divisible by group size {groupsz}."
        num_groups = q_len // groupsz

        def shift(state: "torch.Tensor") -> "torch.Tensor":
            state = torch.cat(
                (state[:, :, : self.num_heads // 2], state[:, :, self.num_heads // 2 :].roll(-groupsz // 2, dims=1)),
                dim=2,
            )
            return state.reshape(bsz * num_groups, groupsz, self.num_heads, self.head_dim)

        query_states, key_states, value_states = shift(query_states), shift(key_states), shift(value_states)
        if attention_mask is not None:
            attention_mask = attention_mask[:, :groupsz].repeat(num_groups, 1)

        attn_output: torch.Tensor = _flash_attention_forward(
            query_states,
            key_states,
            value_states,
            attention_mask,
            query_states.size(1),
            dropout=dropout_rate,
            sliding_window=getattr(self, "sliding_window", None),
            use_top_left_mask=self._flash_attn_uses_top_left_mask,
            is_causal=self.is_causal,
        )

    if getattr(self.config, "group_size_ratio", None) and self.training:  # shift back
        attn_output.reshape(bsz, q_len, self.num_heads, self.head_dim)
        attn_output = torch.cat(
            (
                attn_output[:, :, : self.num_heads // 2],
                attn_output[:, :, self.num_heads // 2 :].roll(groupsz // 2, dims=1),
            ),
            dim=2,
        )

    attn_output = attn_output.reshape(bsz, q_len, self.hidden_size).contiguous()
    attn_output = self.o_proj(attn_output)

    if not output_attentions:
        attn_weights = None

    return attn_output, attn_weights, past_key_value