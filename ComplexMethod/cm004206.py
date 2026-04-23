def forward(
        self,
        pixel_values=None,
        output_attentions=None,
        output_hidden_states=None,
        interpolate_pos_encoding=False,
        return_dict=None,
        **kwargs,
    ) -> tuple | MaskFormerSwinModelOutputWithPooling:
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        if pixel_values is None:
            raise ValueError("You have to specify pixel_values")

        embedding_output, input_dimensions = self.embeddings(
            pixel_values, interpolate_pos_encoding=interpolate_pos_encoding
        )

        encoder_outputs = self.encoder(
            embedding_output,
            input_dimensions,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )

        sequence_output = encoder_outputs.last_hidden_state if return_dict else encoder_outputs[0]
        sequence_output = self.layernorm(sequence_output)

        pooled_output = None
        if self.pooler is not None:
            pooled_output = self.pooler(sequence_output.transpose(1, 2))
            pooled_output = torch.flatten(pooled_output, 1)

        if not return_dict:
            return (sequence_output, pooled_output) + encoder_outputs[1:]

        hidden_states_spatial_dimensions = (input_dimensions,) + encoder_outputs.hidden_states_spatial_dimensions

        return MaskFormerSwinModelOutputWithPooling(
            last_hidden_state=sequence_output,
            pooler_output=pooled_output,
            hidden_states=encoder_outputs.hidden_states,
            hidden_states_spatial_dimensions=hidden_states_spatial_dimensions,
            attentions=encoder_outputs.attentions,
        )