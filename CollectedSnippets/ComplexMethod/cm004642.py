def forward(
        self,
        inputs_embeds=None,
        attention_mask=None,
        encoder_hidden_states=None,
        encoder_attention_mask=None,
        spatial_position_embeddings=None,
        object_queries_position_embeddings=None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> ConditionalDetrDecoderOutput:
        r"""
        Args:
            inputs_embeds (`torch.FloatTensor` of shape `(batch_size, sequence_length, hidden_size)`):
                The query embeddings that are passed into the decoder.

            attention_mask (`torch.Tensor` of shape `(batch_size, sequence_length)`, *optional*):
                Mask to avoid performing attention on certain queries. Mask values selected in `[0, 1]`:

                - 1 for queries that are **not masked**,
                - 0 for queries that are **masked**.

                [What are attention masks?](../glossary#attention-mask)
            encoder_hidden_states (`torch.FloatTensor` of shape `(batch_size, encoder_sequence_length, hidden_size)`, *optional*):
                Sequence of hidden-states at the output of the last layer of the encoder. Used in the cross-attention
                of the decoder.
            encoder_attention_mask (`torch.LongTensor` of shape `(batch_size, encoder_sequence_length)`, *optional*):
                Mask to avoid performing cross-attention on padding pixel_values of the encoder. Mask values selected
                in `[0, 1]`:

                - 1 for pixels that are real (i.e. **not masked**),
                - 0 for pixels that are padding (i.e. **masked**).

            spatial_position_embeddings (`torch.FloatTensor` of shape `(batch_size, sequence_length, hidden_size)`, *optional*):
                Spatial position embeddings that are added to the queries and keys in each cross-attention layer.
            object_queries_position_embeddings (`torch.FloatTensor` of shape `(batch_size, num_queries, hidden_size)`):
                , *optional*): Position embeddings that are added to the queries and keys in each self-attention layer.
        """
        if inputs_embeds is not None:
            hidden_states = inputs_embeds

        # expand encoder attention mask
        if encoder_hidden_states is not None and encoder_attention_mask is not None:
            # [batch_size, seq_len] -> [batch_size, 1, target_seq_len, source_seq_len]
            encoder_attention_mask = create_bidirectional_mask(
                self.config,
                inputs_embeds,
                encoder_attention_mask,
            )

        # optional intermediate hidden states
        intermediate = () if self.config.auxiliary_loss else None

        reference_points_before_sigmoid = self.ref_point_head(
            object_queries_position_embeddings
        )  # [num_queries, batch_size, 2]
        reference_points = reference_points_before_sigmoid.sigmoid().transpose(0, 1)
        obj_center = reference_points[..., :2].transpose(0, 1)
        # get sine embedding for the query vector
        query_sine_embed_before_transformation = gen_sine_position_embeddings(obj_center, self.config.d_model)

        for idx, decoder_layer in enumerate(self.layers):
            if self.training:
                dropout_probability = torch.rand([])
                if dropout_probability < self.layerdrop:
                    continue
            if idx == 0:
                pos_transformation = 1
            else:
                pos_transformation = self.query_scale(hidden_states)
            # apply transformation
            query_sine_embed = query_sine_embed_before_transformation * pos_transformation

            hidden_states = decoder_layer(
                hidden_states,
                None,
                spatial_position_embeddings,
                object_queries_position_embeddings,
                query_sine_embed,
                encoder_hidden_states,  # as a positional argument for gradient checkpointing
                encoder_attention_mask=encoder_attention_mask,
                is_first=(idx == 0),
                **kwargs,
            )

            if self.config.auxiliary_loss:
                hidden_states = self.layernorm(hidden_states)
                intermediate += (hidden_states,)

        # finally, apply layernorm
        hidden_states = self.layernorm(hidden_states)

        # stack intermediate decoder activations
        if self.config.auxiliary_loss:
            intermediate = torch.stack(intermediate)

        return ConditionalDetrDecoderOutput(
            last_hidden_state=hidden_states,
            intermediate_hidden_states=intermediate,
            reference_points=reference_points,
        )