def forward(
        self,
        hidden_states,
        mask=None,
        position_bias=None,
        output_attentions=False,
    ):
        batch_size, seq_length = hidden_states.shape[:2]

        def shape(states):
            """projection"""
            return states.view(batch_size, -1, self.n_heads, self.key_value_proj_dim)

        def unshape(states):
            """reshape"""
            return states.contiguous().view(batch_size, -1, self.inner_dim)

        # Prepare components for transient-global attention
        # Obtain block_ids and global_segment_ids
        # global_seq_len := seq_len // self.global_block_size
        # shapes: (batch_size, seq_len) & (batch_size, global_seq_len)
        block_ids, global_segment_ids = _make_global_fixed_block_ids(
            mask if mask is not None else torch.ones(hidden_states.shape[:-1]),
            self.global_block_size,
        )
        # Create global inputs
        _global_seq_len = global_segment_ids.shape[-1]
        global_inputs = _create_global_aggregates(hidden_states, block_ids, _global_seq_len)
        global_inputs = self.global_input_layer_norm(global_inputs)

        # get query states -> (batch_size, seq_length, n_heads, dim_per_head)
        query_states = shape(self.q(hidden_states))
        key_states = shape(self.k(hidden_states))
        value_states = shape(self.v(hidden_states))
        # Get global/side key/value states  shape: (batch_size, global_seq_len, n_heads, dim_per_head)
        side_key_states = shape(self.k(global_inputs))
        side_value_states = shape(self.v(global_inputs))

        # Split into blocks -> (batch_size, num_blocks, block_len, n_heads, dim_per_head)
        query_states = _split_into_blocks(query_states, self.block_len, dim=1)
        key_states = _split_into_blocks(key_states, self.block_len, dim=1)
        value_states = _split_into_blocks(value_states, self.block_len, dim=1)

        # Concatenate 3 blocks for keys and values -> (batch_size, num_blocks, 3 * block_len, n_heads, dim_per_head)
        key_states = _concatenate_3_blocks(key_states, block_dim=1, sequence_dim=2)
        value_states = _concatenate_3_blocks(value_states, block_dim=1, sequence_dim=2)

        # Tile side inputs across local key/value blocks
        # New shape: (batch_size, num_blocks, global_seq_len, n_heads, dim_per_head)
        reps = [1] * (side_key_states.ndim + 1)
        reps[1] = key_states.shape[1]
        side_key_states = side_key_states.unsqueeze(1).repeat(reps)
        side_value_states = side_value_states.unsqueeze(1).repeat(reps)

        # Concatenate "local" and "side"/"global" key/value states to allow each token to attend global aggregated ones
        # New shape: (batch_size, num_blocks, 3 * block_len + global_seq_len, n_heads, dim_per_head)
        key_states = torch.cat([key_states, side_key_states], dim=2)
        value_states = torch.cat([value_states, side_value_states], dim=2)

        # Compute scores -> (batch_size, num_block, n_heads, block_len, 3 * block_len + global_seq_len)
        scores = torch.einsum("...qhd,...khd->...hqk", query_states, key_states)

        if mask is not None:
            # We need to adjust position bias shape to be sum with mask
            local_attention_mask = _get_local_attention_mask(mask, self.block_len, hidden_states.device)
            # Replace masked positions with -10_000 (according to the original implementation)
            local_attention_mask = torch.where(local_attention_mask > 0, 0.0, -1e10)
        else:
            local_attention_mask = None

        if position_bias is None:
            # position_bias shape: # (1, 1, n_heads, block_len, 3 * block_len)
            if not self.has_relative_attention_bias:
                position_bias = torch.zeros(
                    (1, 1, self.n_heads, self.block_len, 3 * self.block_len),
                    device=scores.device,
                    dtype=scores.dtype,
                )
                if self.gradient_checkpointing and self.training:
                    position_bias.requires_grad = True
            else:
                position_bias = self.compute_bias(self.block_len)

            if local_attention_mask is not None:
                # (batch_size, 1, n_heads, block_len, 3 * block_len)
                position_bias = position_bias + local_attention_mask.transpose(1, 2)
            position_bias = position_bias.type(scores.dtype)

            # Calculate global/side bias - shape: # (batch_size, num_heads, seq_len, global_seq_len)
            if mask is None:
                mask = torch.ones(batch_size, seq_length)
            # (batch_size, num_heads, seq_len, global_seq_len)
            side_position_bias = self.compute_side_bias(mask, global_segment_ids)
            # (batch_size, num_blocks, num_heads, block_len, global_seq_len)
            side_position_bias = _split_into_blocks(side_position_bias, self.block_len, dim=-2).transpose(1, 2)
            side_position_bias = side_position_bias.type(scores.dtype).to(scores.device)
            # (batch_size, num_blocks, num_heads, block_len, 3 * block_len + global_seq_len)
            position_bias = torch.cat([position_bias, side_position_bias], dim=-1)

        scores += position_bias
        # (batch_size, num_blocks, n_heads, block_len, 3 * block_len + global_seq_len)
        attn_weights = nn.functional.softmax(scores.float(), dim=-1).type_as(scores)
        attn_weights = nn.functional.dropout(attn_weights, p=self.dropout, training=self.training)

        attn_weights = attn_weights.type(value_states.dtype)
        attn_output = unshape(torch.einsum("...hqk,...khd->...qhd", attn_weights, value_states))
        attn_output = attn_output[:, :seq_length, :]
        attn_output = self.o(attn_output)

        outputs = (attn_output, position_bias)

        if output_attentions:
            outputs = outputs + (attn_weights,)
        return outputs