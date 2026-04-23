def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        attention_mask: torch.Tensor | None = None,
        encoder_hidden_states: torch.FloatTensor | None = None,
        encoder_attention_mask: torch.LongTensor | None = None,
        past_key_values: Cache | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        use_cache: bool | None = None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> tuple | BaseModelOutputWithPast:
        r"""
        input_ids (`torch.LongTensor` of shape `(batch_size * num_codebooks, sequence_length)`):
            Indices of input sequence tokens in the vocabulary, corresponding to the sequence of audio codes.

            Indices can be obtained by encoding an audio prompt with an audio encoder model to predict audio codes,
            such as with the [`EncodecModel`]. See [`EncodecModel.encode`] for details.

            [What are input IDs?](../glossary#input-ids)

            <Tip warning={true}>

            The `input_ids` will automatically be converted from shape `(batch_size * num_codebooks,
            target_sequence_length)` to `(batch_size, num_codebooks, target_sequence_length)` in the forward pass. If
            you obtain audio codes from an audio encoding model, such as [`EncodecModel`], ensure that the number of
            frames is equal to 1, and that you reshape the audio codes from `(frames, batch_size, num_codebooks,
            target_sequence_length)` to `(batch_size * num_codebooks, target_sequence_length)` prior to passing them as
            `input_ids`.

            </Tip>
        encoder_hidden_states (`torch.FloatTensor` of shape `(batch_size, encoder_sequence_length, hidden_size)`, *optional*):
            Sequence of hidden-states representing the concatenation of the text encoder output and the processed audio encoder output.
            Used as a conditional signal and will thus be concatenated to the projected `decoder_input_ids`.
        encoder_attention_mask (`torch.LongTensor` of shape `(batch_size, encoder_sequence_length)`, *optional*):
            Mask to avoid performing attention on conditional hidden states. Mask values
            selected in `[0, 1]`:

            - 1 for tokens that are **not masked**,
            - 0 for tokens that are **masked**.

            [What are attention masks?](../glossary#attention-mask)
        """
        # retrieve input_ids and inputs_embeds
        if input_ids is not None and inputs_embeds is not None:
            raise ValueError("You cannot specify both decoder_input_ids and decoder_inputs_embeds at the same time")
        elif input_ids is not None:
            # (bsz * codebooks, seq_len) -> (bsz, codebooks, seq_len)
            input = input_ids.reshape(-1, self.num_codebooks, input_ids.shape[-1])
            bsz, num_codebooks, seq_len = input.shape
        elif inputs_embeds is not None:
            input = inputs_embeds[:, :, -1:]
        else:
            raise ValueError("You have to specify either decoder_input_ids or decoder_inputs_embeds")

        if use_cache and past_key_values is None:
            past_key_values = EncoderDecoderCache(DynamicCache(config=self.config), DynamicCache(config=self.config))

        past_key_values_length = past_key_values.get_seq_length() if past_key_values is not None else 0
        if inputs_embeds is None:
            inputs_embeds = sum(self.embed_tokens[codebook](input[:, codebook]) for codebook in range(num_codebooks))

        if encoder_hidden_states is not None:
            # take care of attention masks
            if encoder_attention_mask is not None and attention_mask is None:
                attention_mask = torch.ones(inputs_embeds.shape[:2], device=inputs_embeds.device)

            if attention_mask is not None:
                if encoder_attention_mask is None:
                    encoder_attention_mask = torch.ones(encoder_hidden_states.shape[:2], device=attention_mask.device)
                attention_mask = torch.cat([encoder_attention_mask, attention_mask], dim=1)

            # fuse encoder_hidden_states and inputs_embeds
            inputs_embeds = torch.cat([encoder_hidden_states, inputs_embeds], dim=1)

        attention_mask = create_causal_mask(
            config=self.config,
            inputs_embeds=inputs_embeds,
            attention_mask=attention_mask,
            past_key_values=past_key_values,
        )

        # embed positions
        positions = self.embed_positions(inputs_embeds, past_key_values_length)
        hidden_states = inputs_embeds + positions.to(inputs_embeds.device)
        hidden_states = nn.functional.dropout(hidden_states, p=self.dropout, training=self.training)

        # decoder layers
        for idx, decoder_layer in enumerate(self.layers):
            # add LayerDrop (see https://huggingface.co/papers/1909.11556 for description)
            dropout_probability = random.uniform(0, 1)
            if self.training and (dropout_probability < self.layerdrop):
                continue

            layer_outputs = decoder_layer(
                hidden_states,
                attention_mask=attention_mask,
                past_key_values=past_key_values,
                use_cache=use_cache,
                **kwargs,
            )
            hidden_states = layer_outputs[0]

        hidden_states = self.layer_norm(hidden_states)

        return BaseModelOutputWithPast(
            last_hidden_state=hidden_states,
            past_key_values=past_key_values,
        )