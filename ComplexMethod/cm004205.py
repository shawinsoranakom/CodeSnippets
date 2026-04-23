def forward(
        self,
        hidden_states,
        input_dimensions,
        output_attentions=False,
        output_hidden_states=False,
        return_dict=True,
    ) -> tuple | MaskFormerSwinBaseModelOutput:
        all_hidden_states = () if output_hidden_states else None
        all_input_dimensions = ()
        all_self_attentions = () if output_attentions else None

        if output_hidden_states:
            all_hidden_states = all_hidden_states + (hidden_states,)

        for i, layer_module in enumerate(self.layers):
            layer_hidden_states, output_dimensions, layer_all_hidden_states = layer_module(
                hidden_states,
                input_dimensions,
                output_attentions,
                output_hidden_states,
            )

            input_dimensions = (output_dimensions[-2], output_dimensions[-1])
            all_input_dimensions += (input_dimensions,)
            if output_hidden_states:
                all_hidden_states += (layer_all_hidden_states,)

            hidden_states = layer_hidden_states

            if output_attentions:
                all_self_attentions = all_self_attentions + (layer_all_hidden_states[1],)

        if not return_dict:
            return tuple(v for v in [hidden_states, all_hidden_states, all_self_attentions] if v is not None)

        return MaskFormerSwinBaseModelOutput(
            last_hidden_state=hidden_states,
            hidden_states=all_hidden_states,
            hidden_states_spatial_dimensions=all_input_dimensions,
            attentions=all_self_attentions,
        )