def forward(
        self,
        hidden_states,
        attention_mask=None,
        position_bias=None,
        output_attentions=False,
    ):
        """
        Self-attention block
        """
        # Input is (batch_size, seq_length, dim)
        # Mask is (batch_size, key_length) (non-causal) or (batch_size, key_length, key_length)
        batch_size, seq_length = hidden_states.shape[:2]

        def to_projection_shape(states):
            """projection"""
            return states.contiguous().view(batch_size, -1, self.n_heads, self.key_value_proj_dim).transpose(1, 2)

        # get query states
        # (batch_size, n_heads, seq_length, dim_per_head)
        query_states = to_projection_shape(self.query(hidden_states))

        # get key/value states
        key_states = to_projection_shape(self.key(hidden_states))
        value_states = to_projection_shape(self.value(hidden_states))

        # compute scores
        # equivalent of torch.einsum("bnqd,bnkd->bnqk", query_states, key_states), compatible with onnx op>9
        scores = torch.matmul(query_states, key_states.transpose(3, 2))

        if position_bias is None:
            position_bias = torch.zeros(
                (1, self.n_heads, seq_length, seq_length), device=scores.device, dtype=scores.dtype
            )
            if self.gradient_checkpointing and self.training:
                position_bias.requires_grad = True

            if attention_mask.dim() == 2:
                position_bias = position_bias + attention_mask[:, None, None, :].to(position_bias.device)
            elif attention_mask is not None:
                # (batch_size, n_heads, seq_length, key_length)
                position_bias = position_bias + attention_mask.to(position_bias.device)
            elif not is_torchdynamo_compiling():
                attention_mask = torch.ones(
                    (batch_size, seq_length), device=position_bias.device, dtype=position_bias.dtype
                )
                position_bias = position_bias + attention_mask.to(position_bias.device)

            position_bias = 1 - position_bias

        position_bias_masked = position_bias.masked_fill(position_bias == 1, torch.finfo(scores.dtype).min)
        scores += position_bias_masked
        scores = torch.max(scores, torch.tensor(torch.finfo(scores.dtype).min))

        # (batch_size, n_heads, seq_length, key_length)
        attn_weights = nn.functional.softmax(scores, dim=-1, dtype=torch.float32).type_as(scores)

        # (batch_size, n_heads, seq_length, key_length)
        attn_weights = nn.functional.dropout(attn_weights, p=self.dropout, training=self.training)

        attn_output = torch.matmul(attn_weights, value_states)

        # (batch_size, seq_length, dim)
        attn_output = attn_output.transpose(1, 2).contiguous().view(batch_size, -1, self.inner_dim)

        attn_output = self.output(attn_output)

        outputs = (attn_output,) + (position_bias,)

        if output_attentions:
            outputs = outputs + (attn_weights,)
        return outputs