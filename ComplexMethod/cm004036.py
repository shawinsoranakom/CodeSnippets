def forward(
        self,
        hidden_states: torch.Tensor,
        attention_mask: torch.Tensor,
        output_hidden_states: bool = True,
        output_attentions: bool = False,
        query_states=None,
        relative_pos=None,
        return_dict: bool = True,
    ):
        attention_mask = self.get_attention_mask(attention_mask)
        relative_pos = self.get_rel_pos(hidden_states, query_states, relative_pos)

        all_hidden_states: tuple[torch.Tensor] | None = (hidden_states,) if output_hidden_states else None
        all_attentions = () if output_attentions else None

        next_kv = hidden_states

        rel_embeddings = self.get_rel_embedding()
        for i, layer_module in enumerate(self.layer):
            hidden_states, att_m = layer_module(
                next_kv,
                attention_mask,
                query_states=query_states,
                relative_pos=relative_pos,
                rel_embeddings=rel_embeddings,
                output_attentions=output_attentions,
            )

            if output_hidden_states:
                all_hidden_states = all_hidden_states + (hidden_states,)

            if query_states is not None:
                query_states = hidden_states
            else:
                next_kv = hidden_states

            if output_attentions:
                all_attentions = all_attentions + (att_m,)

        if not return_dict:
            return tuple(v for v in [hidden_states, all_hidden_states, all_attentions] if v is not None)
        return BaseModelOutput(
            last_hidden_state=hidden_states, hidden_states=all_hidden_states, attentions=all_attentions
        )