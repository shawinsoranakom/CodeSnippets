def forward(
        self,
        word_hidden_states,
        entity_hidden_states,
        attention_mask=None,
        output_attentions=False,
        output_hidden_states=False,
        return_dict=True,
    ):
        all_word_hidden_states = () if output_hidden_states else None
        all_entity_hidden_states = () if output_hidden_states else None
        all_self_attentions = () if output_attentions else None

        for i, layer_module in enumerate(self.layer):
            if output_hidden_states:
                all_word_hidden_states = all_word_hidden_states + (word_hidden_states,)
                all_entity_hidden_states = all_entity_hidden_states + (entity_hidden_states,)

            layer_outputs = layer_module(
                word_hidden_states,
                entity_hidden_states,
                attention_mask,
                output_attentions,
            )

            word_hidden_states = layer_outputs[0]

            if entity_hidden_states is not None:
                entity_hidden_states = layer_outputs[1]

            if output_attentions:
                all_self_attentions = all_self_attentions + (layer_outputs[2],)

        if output_hidden_states:
            all_word_hidden_states = all_word_hidden_states + (word_hidden_states,)
            all_entity_hidden_states = all_entity_hidden_states + (entity_hidden_states,)

        if not return_dict:
            return tuple(
                v
                for v in [
                    word_hidden_states,
                    all_word_hidden_states,
                    all_self_attentions,
                    entity_hidden_states,
                    all_entity_hidden_states,
                ]
                if v is not None
            )
        return BaseLukeModelOutput(
            last_hidden_state=word_hidden_states,
            hidden_states=all_word_hidden_states,
            attentions=all_self_attentions,
            entity_last_hidden_state=entity_hidden_states,
            entity_hidden_states=all_entity_hidden_states,
        )