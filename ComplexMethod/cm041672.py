def llama_sdpa_attention_forward(
    self: "LlamaSdpaAttention",
    hidden_states: "torch.Tensor",
    attention_mask: Optional["torch.Tensor"] = None,
    position_ids: Optional["torch.LongTensor"] = None,
    past_key_value: Optional["Cache"] = None,
    output_attentions: bool = False,
    cache_position: Optional["torch.LongTensor"] = None,
    position_embeddings: Optional[tuple["torch.Tensor", "torch.Tensor"]] = None,
    **kwargs,
) -> tuple["torch.Tensor", Optional["torch.Tensor"], Optional[tuple["torch.Tensor"]]]:
    if output_attentions:
        transformers_logger.warning_once(
            "SDPA does not support `output_attentions=True`. Falling back to the vanilla attention"
        )
        return llama_attention_forward(
            self,
            hidden_states=hidden_states,
            attention_mask=attention_mask,
            position_ids=position_ids,
            past_key_value=past_key_value,
            output_attentions=output_attentions,
            cache_position=cache_position,
            **kwargs,
        )

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

    if getattr(self.config, "group_size_ratio", None) and self.training:  # shift
        groupsz = int(q_len * getattr(self.config, "group_size_ratio"))
        assert q_len % groupsz == 0, f"q_len {q_len} should be divisible by group size {groupsz}."
        num_groups = q_len // groupsz

        def shift(state: "torch.Tensor") -> "torch.Tensor":
            state = state.transpose(1, 2)  # output: (bsz, seq_len, n_heads, head_dim)
            state = torch.cat(
                (state[:, :, : self.num_heads // 2], state[:, :, self.num_heads // 2 :].roll(-groupsz // 2, dims=1)),
                dim=2,
            )
            return state.reshape(bsz * num_groups, groupsz, self.num_heads, self.head_dim).transpose(1, 2)

        query_states, key_states, value_states = shift(query_states), shift(key_states), shift(value_states)
        if attention_mask is not None:
            attention_mask = attention_mask[:, :, :groupsz, :groupsz].repeat(num_groups, 1, 1, 1)

    causal_mask = attention_mask
    if attention_mask is not None:
        causal_mask = causal_mask[:, :, :, : key_states.shape[-2]]

    if query_states.device.type == "cuda" and causal_mask is not None:  # avoid pytorch bug
        query_states = query_states.contiguous()
        key_states = key_states.contiguous()
        value_states = value_states.contiguous()

    is_causal = True if causal_mask is None and q_len > 1 else False
    attn_output = torch.nn.functional.scaled_dot_product_attention(
        query_states,
        key_states,
        value_states,
        attn_mask=causal_mask,
        dropout_p=self.attention_dropout if self.training else 0.0,
        is_causal=is_causal,
    )
    attn_output = attn_output.transpose(1, 2).contiguous()

    if getattr(self.config, "group_size_ratio", None) and self.training:  # shift back
        attn_output.reshape(bsz, q_len, self.num_heads, self.head_dim)
        attn_output = torch.cat(
            (
                attn_output[:, :, : self.num_heads // 2],
                attn_output[:, :, self.num_heads // 2 :].roll(groupsz // 2, dims=1),
            ),
            dim=2,
        )

    attn_output = attn_output.reshape(bsz, q_len, self.hidden_size)
    attn_output = self.o_proj(attn_output)

    return attn_output, None, past_key_value