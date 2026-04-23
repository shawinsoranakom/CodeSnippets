def forward(
        self,
        inputs_embeds: torch.Tensor | None = None,
        multi_stage_positional_embeddings: torch.Tensor | None = None,
        pixel_embeddings: torch.Tensor | None = None,
        encoder_hidden_states: torch.Tensor | None = None,
        query_position_embeddings: torch.Tensor | None = None,
        feature_size_list: list | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
    ):
        r"""
        Args:
            inputs_embeds (`torch.FloatTensor` of shape `(num_queries, batch_size, hidden_size)`):
                The query embeddings that are passed into the decoder.
            multi_stage_positional_embeddings (`torch.FloatTensor` of shape `(height*width, batch_size, num_channels)`):
                Position embeddings that are added to the keys in each cross(masked)-attention layer.
            pixel_embeddings (`torch.FloatTensor`):
                Tensor of shape `(batch_size, num_channels, height, width)`, 1/4 scale features from the last Pixel
                Decoder.
            query_position_embeddings (`torch.FloatTensor` of shape `(num_queries, batch_size, hidden_size)`):
                , *optional*): Position embeddings that are added to the queries and keys in each self-attention layer.
            encoder_hidden_states (`torch.FloatTensor` of shape `(batch_size, encoder_sequence_length, hidden_size)`):
                Sequence of hidden-states at the output of the last layer of the encoder. Used in the
                cross(masked)-attention of the decoder.
            feature_size_list (`list[torch.Size]`):
                This is a list containing shapes (height & width) of multi-scale features from the Pixel Decoder.
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

        if inputs_embeds is not None:
            hidden_states = inputs_embeds

        # intermediate hidden states with layernorm applied - required for predicting class logits
        intermediate = ()

        # decoder layers
        all_hidden_states = () if output_hidden_states else None
        attentions = () if output_attentions else None

        # intermediate mask predictions from transformer decoder layers
        intermediate_mask_predictions = ()

        intermediate_hidden_states = self.layernorm(inputs_embeds)
        intermediate += (intermediate_hidden_states,)

        predicted_mask, attention_mask = self.mask_predictor(
            intermediate_hidden_states, pixel_embeddings, feature_size_list[0]
        )
        intermediate_mask_predictions += (predicted_mask,)

        for idx, decoder_layer in enumerate(self.layers):
            if output_hidden_states:
                all_hidden_states += (hidden_states,)

            dropout_probability = torch.rand([])

            if self.training and (dropout_probability < self.layerdrop):
                continue

            level_index = idx % self.num_feature_levels

            where = (attention_mask.sum(-1) != attention_mask.shape[-1]).to(attention_mask.dtype)
            # Multiply the attention mask instead of indexing to avoid issue in torch.export.
            attention_mask = attention_mask * where.unsqueeze(-1)

            layer_outputs = decoder_layer(
                hidden_states,
                level_index,
                None,  # attention_mask
                multi_stage_positional_embeddings,
                query_position_embeddings,
                encoder_hidden_states,  # as a positional argument for gradient checkpointing
                encoder_attention_mask=attention_mask,
                output_attentions=output_attentions,
            )

            intermediate_hidden_states = self.layernorm(layer_outputs[0])

            predicted_mask, attention_mask = self.mask_predictor(
                intermediate_hidden_states,
                pixel_embeddings,
                feature_size_list[(idx + 1) % self.num_feature_levels],
            )

            intermediate_mask_predictions += (predicted_mask,)

            # add intermediate hidden states with layer norm applied which will be used for predicting class logits
            intermediate += (intermediate_hidden_states,)

            hidden_states = layer_outputs[0]

            if output_attentions:
                attentions += (layer_outputs[1],)

        # add hidden states from the last decoder layer
        if output_hidden_states:
            all_hidden_states += (hidden_states,)

        hidden_states = hidden_states.transpose(1, 0)
        if not return_dict:
            outputs = [hidden_states, all_hidden_states, attentions, intermediate, intermediate_mask_predictions]
            return tuple(v for v in outputs if v is not None)

        return Mask2FormerMaskedAttentionDecoderOutput(
            last_hidden_state=hidden_states,
            hidden_states=all_hidden_states,
            attentions=attentions,
            intermediate_hidden_states=intermediate,
            masks_queries_logits=intermediate_mask_predictions,
        )