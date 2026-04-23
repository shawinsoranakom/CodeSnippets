def forward(
        self,
        pixel_values: torch.FloatTensor,
        output_attentions: bool | None = False,
        output_hidden_states: bool | None = False,
        return_dict: bool | None = True,
    ) -> tuple | BaseModelOutput:
        all_hidden_states = () if output_hidden_states else None
        all_self_attentions = () if output_attentions else None

        batch_size = pixel_values.shape[0]
        hidden_states = pixel_values
        for idx, layer in enumerate(self.layers):
            layer_output = layer(hidden_states, output_attentions)
            outputs, height, width = layer_output
            hidden_states = outputs[0]
            if output_attentions:
                all_self_attentions = all_self_attentions + (outputs[1],)
            # reshape back to (batch_size, num_channels, height, width)
            hidden_states = hidden_states.reshape(batch_size, height, width, -1).permute(0, 3, 1, 2).contiguous()
            if output_hidden_states:
                all_hidden_states = all_hidden_states + (hidden_states,)
        if not return_dict:
            return tuple(v for v in [hidden_states, all_hidden_states, all_self_attentions] if v is not None)
        return BaseModelOutput(
            last_hidden_state=hidden_states,
            hidden_states=all_hidden_states,
            attentions=all_self_attentions,
        )