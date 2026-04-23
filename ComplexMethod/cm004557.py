def forward(
        self,
        hidden_states: torch.Tensor,
        pos_emb: torch.Tensor | None = None,
        attention_mask: torch.Tensor | None = None,
        output_attentions: torch.Tensor | None = False,
    ):
        """
        Compute encoded features.

        Args:
            hidden_states (`torch.Tensor` of shape `(batch, time, size)`): Input tensor.
            pos_emb (`torch.Tensor` of shape `(1, time, size)`): Positional embeddings tensor.
            attention_mask (`torch.Tensor` of shape `(batch, time)`): Attention mask tensor for the input.
            output_attentions (`bool`, *optional*):
                Whether or not to return the attentions tensors of all attention layers. See `attentions` under
                returned tensors for more detail.
        Returns:
            `torch.Tensor`: Output tensor of shape `(batch, time, size)`.

        """
        # whether to use macaron style
        if self.macaron_style:
            residual = hidden_states
            if self.normalize_before:
                hidden_states = self.ff_macaron_layer_norm(hidden_states)
            hidden_states = residual + self.ff_scale * self.dropout(self.feed_forward_macaron(hidden_states))
            if not self.normalize_before:
                hidden_states = self.ff_macaron_layer_norm(hidden_states)

        # multi-headed self-attention module
        residual = hidden_states
        if self.normalize_before:
            hidden_states = self.self_attn_layer_norm(hidden_states)

        attention_output, attention_scores = self.self_attn(
            hidden_states, attention_mask=attention_mask, pos_emb=pos_emb, output_attentions=output_attentions
        )

        if self.concat_after:
            x_concat = torch.cat((hidden_states, attention_output), dim=-1)
            hidden_states = self.concat_linear(x_concat)
            hidden_states = residual + hidden_states
        else:
            hidden_states = self.dropout(attention_output)
            hidden_states = residual + hidden_states
        if not self.normalize_before:
            hidden_states = self.self_attn_layer_norm(hidden_states)

        # convolution module
        if self.use_cnn_module:
            residual = hidden_states
            if self.normalize_before:
                hidden_states = self.conv_layer_norm(hidden_states)
            hidden_states = self.conv_module(hidden_states)
            hidden_states = self.dropout(hidden_states)
            hidden_states = residual + hidden_states
            if not self.normalize_before:
                hidden_states = self.conv_layer_norm(hidden_states)

        # feed forward module
        residual = hidden_states
        if self.normalize_before:
            hidden_states = self.ff_layer_norm(hidden_states)
        hidden_states = self.feed_forward(hidden_states)
        hidden_states = self.dropout(hidden_states)
        hidden_states = residual + self.ff_scale * hidden_states
        if not self.normalize_before:
            hidden_states = self.ff_layer_norm(hidden_states)

        if self.conv_module is not None:
            hidden_states = self.final_layer_norm(hidden_states)

        outputs = (hidden_states,)

        if output_attentions:
            outputs += (attention_scores,)

        return outputs