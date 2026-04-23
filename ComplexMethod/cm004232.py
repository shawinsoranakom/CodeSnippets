def forward(
        self,
        inputs_embeds=None,
        attention_mask=None,
        encoder_hidden_states=None,
        encoder_attention_mask=None,
        spatial_position_embeddings=None,
        object_queries_position_embeddings=None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> DetrDecoderOutput:
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
                Spatial position embeddings (2D positional encodings from encoder) that are added to the keys in each cross-attention layer.
            object_queries_position_embeddings (`torch.FloatTensor` of shape `(batch_size, num_queries, hidden_size)`, *optional*):
                Position embeddings for the object query slots that are added to the queries and keys in each self-attention layer.
        """

        if inputs_embeds is not None:
            hidden_states = inputs_embeds

        if attention_mask is not None:
            attention_mask = create_bidirectional_mask(
                config=self.config,
                inputs_embeds=hidden_states,
                attention_mask=attention_mask,
            )

        # expand encoder attention mask (for cross-attention on encoder outputs)
        if encoder_hidden_states is not None and encoder_attention_mask is not None:
            encoder_attention_mask = create_bidirectional_mask(
                config=self.config,
                inputs_embeds=hidden_states,
                attention_mask=encoder_attention_mask,
                encoder_hidden_states=encoder_hidden_states,
            )

        # optional intermediate hidden states
        intermediate = () if self.config.auxiliary_loss else None

        # decoder layers

        for idx, decoder_layer in enumerate(self.layers):
            hidden_states = decoder_layer(
                hidden_states,
                attention_mask,
                spatial_position_embeddings,
                object_queries_position_embeddings,
                encoder_hidden_states,  # as a positional argument for gradient checkpointing
                encoder_attention_mask=encoder_attention_mask,
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

        return DetrDecoderOutput(last_hidden_state=hidden_states, intermediate_hidden_states=intermediate)