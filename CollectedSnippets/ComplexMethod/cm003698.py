def forward(
        self,
        hidden_states: torch.FloatTensor,
        rotary_pos_emb: torch.FloatTensor | None = None,
        attention_mask: torch.LongTensor | None = None,
        position_ids: torch.LongTensor | None = None,
        past_key_values: Cache | None = None,
        use_cache: bool | None = False,
        **kwargs: Unpack[TransformersKwargs],
    ) -> tuple[torch.FloatTensor, torch.FloatTensor | None]:
        # Raise error when position_ids is None but rotary_pos_emb is provided, because we need that when applying
        # rotary_pos_emb to query and key states.
        if rotary_pos_emb is not None and position_ids is None:
            raise ValueError("`position_ids` must be provided when `rotary_pos_emb` is not None.")

        bsz, _, embed_dim = hidden_states.size()

        # get query proj
        query_states = self._shape(self.q_proj(hidden_states), -1, bsz) * self.scale
        key_states = self._shape(self.k_proj(hidden_states), -1, bsz)
        value_states = self._shape(self.v_proj(hidden_states), -1, bsz)

        if past_key_values is not None:
            key_states, value_states = past_key_values.update(key_states, value_states, self.layer_idx)

        if rotary_pos_emb is not None:
            rotary_emb_dim = rotary_pos_emb.shape[-1]

            # Partial rotary embedding
            query_rot, query_pass = (
                query_states[..., :rotary_emb_dim],
                query_states[..., rotary_emb_dim:],
            )
            key_rot, key_pass = (
                key_states[..., :rotary_emb_dim],
                key_states[..., rotary_emb_dim:],
            )
            value_rot, value_pass = (
                value_states[..., :rotary_emb_dim],
                value_states[..., rotary_emb_dim:],
            )

            cos, sin = rotary_pos_emb.cos().squeeze(0), rotary_pos_emb.sin().squeeze(0)
            query_rot, key_rot, value_rot = apply_rotary_pos_emb(query_rot, key_rot, value_rot, cos, sin, position_ids)

            # [batch_size, num_heads, seq_length, head_dim]
            query_states = torch.cat((query_rot, query_pass), dim=-1)
            key_states = torch.cat((key_rot, key_pass), dim=-1)
            value_states = torch.cat((value_rot, value_pass), dim=-1)

        tgt_len = query_states.shape[2]
        src_len = key_states.shape[2]
        attn_weights = torch.matmul(query_states, key_states.transpose(2, 3))

        if attention_mask is not None:
            if attention_mask.size() != (bsz, 1, tgt_len, src_len):
                raise ValueError(
                    f"Attention mask should be of size {(bsz, 1, tgt_len, src_len)}, but is {attention_mask.size()}"
                )
            attn_weights = attn_weights + attention_mask

        attn_weights = nn.functional.softmax(attn_weights, dim=-1)

        attn_probs = nn.functional.dropout(attn_weights, p=self.dropout, training=self.training)
        attn_output = torch.matmul(attn_probs, value_states)

        if attn_output.size() != (bsz, self.num_heads, tgt_len, self.head_dim):
            raise ValueError(
                f"`attn_output` should be of size {(bsz, self.num_heads, tgt_len, self.head_dim)}, but is"
                f" {attn_output.size()}"
            )

        attn_output = attn_output.transpose(1, 2).contiguous()
        attn_output = attn_output.reshape(bsz, tgt_len, self.embed_dim)

        attn_output = self.out_proj(attn_output)

        return attn_output, attn_weights