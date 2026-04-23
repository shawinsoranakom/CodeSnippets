def forward(
        self,
        hidden_states,
        attention_mask,
        output_hidden_states=True,
        output_attentions=False,
        query_states=None,
        relative_pos=None,
        return_dict=True,
    ):
        if attention_mask.dim() <= 2:
            input_mask = attention_mask
        else:
            input_mask = attention_mask.sum(-2) > 0
        attention_mask = self.get_attention_mask(attention_mask)
        relative_pos = self.get_rel_pos(hidden_states, query_states, relative_pos)

        all_hidden_states: tuple[torch.Tensor] | None = (hidden_states,) if output_hidden_states else None
        all_attentions = () if output_attentions else None

        next_kv = hidden_states
        rel_embeddings = self.get_rel_embedding()
        for i, layer_module in enumerate(self.layer):
            output_states, attn_weights = layer_module(
                next_kv,
                attention_mask,
                query_states=query_states,
                relative_pos=relative_pos,
                rel_embeddings=rel_embeddings,
                output_attentions=output_attentions,
            )

            if output_attentions:
                all_attentions = all_attentions + (attn_weights,)

            if i == 0 and self.conv is not None:
                output_states = self.conv(hidden_states, output_states, input_mask)

            if output_hidden_states:
                all_hidden_states = all_hidden_states + (output_states,)

            if query_states is not None:
                query_states = output_states
                if isinstance(hidden_states, Sequence):
                    next_kv = hidden_states[i + 1] if i + 1 < len(self.layer) else None
            else:
                next_kv = output_states

        if not return_dict:
            return tuple(v for v in [output_states, all_hidden_states, all_attentions] if v is not None)
        return BaseModelOutput(
            last_hidden_state=output_states, hidden_states=all_hidden_states, attentions=all_attentions
        )