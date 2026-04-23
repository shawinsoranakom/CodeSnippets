def forward(
        self,
        hidden_states: torch.Tensor,
        feature_ensemble: bool = False,
        output_attentions: bool = False,
        output_hidden_states: bool = False,
        return_dict: bool = True,
    ) -> tuple | SegGptEncoderOutput:
        all_hidden_states = () if output_hidden_states else None
        all_self_attentions = () if output_attentions else None
        intermediate_hidden_states = []

        for i, layer_module in enumerate(self.layers):
            if output_hidden_states:
                all_hidden_states = all_hidden_states + (hidden_states,)

            # Condition to check if we have the appropriate number of prompts to ensemble
            ensemble_cond = 2 if self.config.merge_index > i else 1

            layer_outputs = layer_module(hidden_states, ensemble_cond, feature_ensemble, output_attentions)

            hidden_states = layer_outputs[0]

            if i == self.config.merge_index:
                hidden_states = (
                    hidden_states[: hidden_states.shape[0] // 2] + hidden_states[hidden_states.shape[0] // 2 :]
                ) * 0.5

            if i in self.config.intermediate_hidden_state_indices:
                intermediate_hidden_states.append(self.layernorm(hidden_states))

            if output_attentions:
                all_self_attentions = all_self_attentions + (layer_outputs[1],)

        if output_hidden_states:
            all_hidden_states = all_hidden_states + (hidden_states,)

        if not return_dict:
            return tuple(
                v
                for v in [hidden_states, all_hidden_states, all_self_attentions, intermediate_hidden_states]
                if v is not None
            )
        return SegGptEncoderOutput(
            last_hidden_state=hidden_states,
            hidden_states=all_hidden_states,
            attentions=all_self_attentions,
            intermediate_hidden_states=intermediate_hidden_states,
        )