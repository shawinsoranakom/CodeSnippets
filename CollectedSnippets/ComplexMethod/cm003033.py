def forward(
        self,
        char_input_ids: torch.LongTensor | None = None,
        char_count_per_id: torch.LongTensor | None = None,
        encoder_hidden_states: torch.FloatTensor | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple | SeamlessM4Tv2TextToUnitDecoderOutput:
        r"""
        Args:
            char_input_ids (`torch.LongTensor` of shape `(batch_size, char_sequence_length)`):
                Character indices. The correspondence between characters and indices can be found in `char_to_id`, a
                dictionary in the generation configuration.
            char_count_per_id (`torch.Tensor` of shape `(batch_size, encoder_sequence_length)`):
                Number of characters per text input id.
            encoder_hidden_states (`torch.FloatTensor` of shape `(batch_size, encoder_sequence_length, hidden_size)`):
                Sequence of hidden-states at the output of the last layer of the encoder. Used in the cross-attention
                of the decoder.
            output_attentions (`bool`, *optional*):
                Whether or not to return the attentions tensors of all attention layers. See `attentions` under
                returned tensors for more detail.
            output_hidden_states (`bool`, *optional*):
                Whether or not to return the hidden states of all layers. See `hidden_states` under returned tensors
                for more detail.
            return_dict (`bool`, *optional*):
                Whether or not to return a [`~utils.ModelOutput`] instead of a plain tuple.
        """
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        # create padding mask for character lengths
        char_padding_mask = _compute_new_attention_mask(char_input_ids, char_count_per_id.sum(1))

        # upsample hidden states according to characters sequence lengths
        char_hidden_states = self._hard_upsample(encoder_hidden_states, char_count_per_id)
        # embed char positions
        char_positions = self.pos_emb_alpha_char * self.embed_char_positions(inputs_embeds=char_hidden_states)
        # update char hidden states with positions and char embeddings
        char_hidden_states = self.embed_char(char_input_ids) * self.embed_scale + char_positions + char_hidden_states

        # predict duration
        log_dur_pred = self.duration_predictor(char_hidden_states, padding_mask=char_padding_mask)
        dur_out = torch.clamp(torch.round(torch.expm1(log_dur_pred)).long(), min=1)
        dur_out = dur_out.masked_fill(~char_padding_mask.bool(), 0.0)

        # upsample char hidden states according to predicted duration
        char_hidden_states = self._hard_upsample(char_hidden_states, dur_out)

        positions = self.pos_emb_alpha * self.embed_positions(inputs_embeds=char_hidden_states)
        hidden_states = char_hidden_states + positions

        padding_mask = _compute_new_attention_mask(hidden_states, dur_out.sum(1))
        attention_mask = create_bidirectional_mask(
            config=self.config,
            inputs_embeds=hidden_states,
            attention_mask=padding_mask,
        )

        hidden_states = nn.functional.dropout(hidden_states, p=self.dropout, training=self.training)

        # decoder layers
        all_hidden_states = () if output_hidden_states else None
        all_self_attns = () if output_attentions else None

        for idx, decoder_layer in enumerate(self.layers):
            # add LayerDrop (see https://huggingface.co/papers/1909.11556 for description)
            if output_hidden_states:
                all_hidden_states += (hidden_states,)
            if self.training:
                dropout_probability = torch.rand([])
                if dropout_probability < self.layerdrop:
                    continue

            layer_outputs = decoder_layer(
                hidden_states,
                attention_mask=attention_mask,
                padding_mask=padding_mask,
                output_attentions=output_attentions,
            )
            hidden_states = layer_outputs[0]

            if output_attentions:
                all_self_attns += (layer_outputs[2],)

        hidden_states = self.layer_norm(hidden_states)

        # add hidden states from the last decoder layer
        if output_hidden_states:
            all_hidden_states += (hidden_states,)

        if not return_dict:
            return tuple(v for v in [hidden_states, all_hidden_states, all_self_attns, padding_mask] if v is not None)
        return SeamlessM4Tv2TextToUnitDecoderOutput(
            last_hidden_state=hidden_states,
            hidden_states=all_hidden_states,
            attentions=all_self_attns,
            padding_mask=padding_mask,
        )