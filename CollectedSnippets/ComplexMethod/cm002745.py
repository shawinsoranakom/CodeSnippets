def forward(
        self,
        pixel_values: torch.Tensor | None = None,
        noise: torch.FloatTensor | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        interpolate_pos_encoding: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple | BaseModelOutputWithPooling:
        r"""
        noise (`torch.FloatTensor` of shape `(batch_size, num_mask_units)`, *optional*):
            Mainly used for testing purposes to control randomness and maintain the reproducibility
        """
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        if pixel_values is None:
            raise ValueError("You have to specify pixel_values")

        embedding_output, bool_masked_pos, ids_restore = self.embeddings(
            pixel_values, interpolate_pos_encoding=interpolate_pos_encoding, noise=noise
        )

        image_shape = (pixel_values.shape[-2], pixel_values.shape[-1])
        hidden_states = unroll(
            embedding_output,
            image_shape=image_shape,
            patch_stride=self.config.patch_stride,
            schedule=self.unroll_schedule,
        )

        # Discard masked tokens if bool_masked_pos is provided
        if bool_masked_pos is not None:
            mask_unit_area = math.prod(self.config.masked_unit_size)
            batch_size, _, hidden_size = hidden_states.shape
            positions = bool_masked_pos.unsqueeze(-1).tile(1, mask_unit_area, hidden_size)
            hidden_states = hidden_states[positions]
            hidden_states = hidden_states.view(batch_size, -1, hidden_size)

        encoder_outputs = self.encoder(
            hidden_states,
            bool_masked_pos=bool_masked_pos,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )
        sequence_output = encoder_outputs[0]
        pooled_output = None
        if self.pooler is not None:
            pooled_output = self.pooler(sequence_output)

        if not return_dict:
            head_outputs = (sequence_output, pooled_output) if pooled_output is not None else (sequence_output,)
            head_outputs = (
                head_outputs + (bool_masked_pos, ids_restore) if bool_masked_pos is not None else head_outputs
            )
            return head_outputs + encoder_outputs[1:]

        return HieraModelOutput(
            last_hidden_state=sequence_output,
            pooler_output=pooled_output,
            bool_masked_pos=bool_masked_pos,
            ids_restore=ids_restore,
            hidden_states=encoder_outputs.hidden_states,
            attentions=encoder_outputs.attentions,
            reshaped_hidden_states=encoder_outputs.reshaped_hidden_states,
        )