def forward(
        self,
        input_data=None,
        bool_masked_pos=None,
        head_mask=None,
        output_attentions=None,
        output_hidden_states=None,
        return_dict=None,
    ) -> Union[Tuple, DonutSwinModelOutput]:
        r"""
        bool_masked_pos (`paddle.BoolTensor` of shape `(batch_size, num_patches)`):
            Boolean masked positions. Indicates which patches are masked (1) and which aren't (0).
        """
        if self.training:
            pixel_values, label, attention_mask = input_data
        else:
            if isinstance(input_data, list):
                pixel_values = input_data[0]
            else:
                pixel_values = input_data
        output_attentions = (
            output_attentions
            if output_attentions is not None
            else self.config.output_attentions
        )
        output_hidden_states = (
            output_hidden_states
            if output_hidden_states is not None
            else self.config.output_hidden_states
        )
        return_dict = (
            return_dict if return_dict is not None else self.config.return_dict
        )

        if pixel_values is None:
            raise ValueError("You have to specify pixel_values")
        num_channels = pixel_values.shape[1]
        if num_channels == 1:
            pixel_values = paddle.repeat_interleave(pixel_values, repeats=3, axis=1)

        head_mask = self.get_head_mask(head_mask, len(self.config.depths))

        embedding_output, input_dimensions = self.embeddings(
            pixel_values, bool_masked_pos=bool_masked_pos
        )

        encoder_outputs = self.encoder(
            embedding_output,
            input_dimensions,
            head_mask=head_mask,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )
        sequence_output = encoder_outputs[0]

        pooled_output = None
        if self.pooler is not None:
            pooled_output = self.pooler(sequence_output.transpose([0, 2, 1]))
            pooled_output = paddle.flatten(pooled_output, 1)

        if not return_dict:
            output = (sequence_output, pooled_output) + encoder_outputs[1:]
            return output

        donut_swin_output = DonutSwinModelOutput(
            last_hidden_state=sequence_output,
            pooler_output=pooled_output,
            hidden_states=encoder_outputs.hidden_states,
            attentions=encoder_outputs.attentions,
            reshaped_hidden_states=encoder_outputs.reshaped_hidden_states,
        )
        if self.training:
            return donut_swin_output, label, attention_mask
        else:
            return donut_swin_output