def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        attention_mask: torch.BoolTensor | None = None,
        input_features: torch.FloatTensor | None = None,
        decoder_input_ids: torch.LongTensor | None = None,
        decoder_attention_mask: torch.BoolTensor | None = None,
        past_key_values: Cache | None = None,
        encoder_hidden_states: torch.FloatTensor | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        decoder_inputs_embeds: torch.FloatTensor | None = None,
        labels: torch.LongTensor | None = None,
        use_cache: bool | None = None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> tuple | MusicgenMelodyOutputWithPast:
        r"""
        decoder_input_ids (`torch.LongTensor` of shape `(batch_size * num_codebooks, target_sequence_length)`, *optional*):
            Indices of decoder input sequence tokens in the vocabulary, corresponding to the sequence of audio codes.

            Indices can be obtained by encoding an audio prompt with an audio encoder model to predict audio codes,
            such as with the [`EncodecModel`]. See [`EncodecModel.encode`] for details.

            [What are decoder input IDs?](../glossary#decoder-input-ids)

            <Tip warning={true}>

            The `decoder_input_ids` will automatically be converted from shape `(batch_size * num_codebooks,
            target_sequence_length)` to `(batch_size, num_codebooks, target_sequence_length)` in the forward pass. If
            you obtain audio codes from an audio encoding model, such as [`EncodecModel`], ensure that the number of
            frames is equal to 1, and that you reshape the audio codes from `(frames, batch_size, num_codebooks,
            target_sequence_length)` to `(batch_size * num_codebooks, target_sequence_length)` prior to passing them as
            `decoder_input_ids`.

            </Tip>
        decoder_attention_mask (`torch.LongTensor` of shape `(batch_size, target_sequence_length)`, *optional*):
            Default behavior: generate a tensor that ignores pad tokens in `decoder_input_ids`. Causal mask will also
            be used by default.
        encoder_hidden_states (`torch.FloatTensor` of shape `(batch_size, encoder_sequence_length, hidden_size)`, *optional*):
            Sequence of conditional hidden-states representing the concatenation of the projected text encoder output and the projected audio encoder output.
            Used as a conditional signal and will thus be concatenated to the projected `decoder_input_ids`.
        labels (`torch.LongTensor` of shape `(batch_size, sequence_length, num_codebooks)`, *optional*):
            Labels for language modeling. Note that the labels **are shifted** inside the model, i.e. you can set
            `labels = input_ids` Indices are selected in `[-100, 0, ..., config.vocab_size]` All labels set to `-100`
            are ignored (masked), the loss is only computed for labels in `[0, ..., config.vocab_size]`

        Examples:
        ```python
        >>> from transformers import AutoProcessor, MusicgenMelodyForConditionalGeneration
        >>> import torch

        >>> processor = AutoProcessor.from_pretrained("facebook/musicgen-melody")
        >>> model = MusicgenMelodyForConditionalGeneration.from_pretrained("facebook/musicgen-melody")

        >>> inputs = processor(
        ...     text=["80s pop track with bassy drums and synth", "90s rock song with loud guitars and heavy drums"],
        ...     padding=True,
        ...     return_tensors="pt",
        ... )

        >>> pad_token_id = model.generation_config.pad_token_id
        >>> decoder_input_ids = (
        ...     torch.ones((inputs.input_ids.shape[0] * model.decoder.num_codebooks, 1), dtype=torch.long)
        ...     * pad_token_id
        ... )

        >>> logits = model(**inputs, decoder_input_ids=decoder_input_ids).logits
        >>> logits.shape  # (bsz * num_codebooks, encoder_len + tgt_len, vocab_size)
        torch.Size([8, 249, 2048])
        ```"""
        kwargs_text_encoder = {
            argument[len("text_encoder_")]: value
            for argument, value in kwargs.items()
            if argument.startswith("text_encoder_")
        }

        kwargs_decoder = {
            argument[len("decoder_") :]: value for argument, value in kwargs.items() if argument.startswith("decoder_")
        }

        for passthrough_key in ("output_attentions", "output_hidden_states"):
            if passthrough_key in kwargs:
                kwargs_text_encoder[passthrough_key] = kwargs[passthrough_key]
                kwargs_decoder[passthrough_key] = kwargs[passthrough_key]

        if encoder_hidden_states is None:
            if inputs_embeds is not None or input_ids is not None:
                encoder_outputs = self.text_encoder(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    inputs_embeds=inputs_embeds,
                    **kwargs_text_encoder,
                )

                encoder_hidden_states = encoder_outputs[0]

                # optionally project encoder_hidden_states
                if self.text_encoder.config.hidden_size != self.decoder.config.hidden_size:
                    encoder_hidden_states = self.enc_to_dec_proj(encoder_hidden_states)

            if attention_mask is not None and encoder_hidden_states is not None:
                encoder_hidden_states = encoder_hidden_states * attention_mask[..., None]

            # set a default audio conditional hidden states if text is not None
            if encoder_hidden_states is not None and input_features is None:
                input_features = torch.zeros(
                    (encoder_hidden_states.shape[0], 1, self.config.num_chroma),
                    device=self.device,
                    dtype=self.dtype,
                )
                input_features[:, :, 0] = 1

            if input_features is not None:
                audio_hidden_states = input_features

                # optionally project audio_hidden_states ->
                # (batch_size, seq_len, num_chroma) -> (batch_size, seq_len, hidden_size)
                if self.config.num_chroma != self.decoder.config.hidden_size:
                    audio_hidden_states = self.audio_enc_to_dec_proj(audio_hidden_states)

                # pad or truncate to config.chroma_length
                if audio_hidden_states.shape[1] < self.config.chroma_length:
                    n_repeat = int(math.ceil(self.config.chroma_length / audio_hidden_states.shape[1]))
                    audio_hidden_states = audio_hidden_states.repeat(1, n_repeat, 1)
                else:
                    logger.warning(
                        f"The conditional audio signal is of length {audio_hidden_states.shape[1]}, which exceeds"
                        f"the maximum chroma duration of {self.config.chroma_length}."
                        f"The audio will be truncated to {self.config.chroma_length} frames."
                    )
                audio_hidden_states = audio_hidden_states[:, : self.config.chroma_length]

                if encoder_hidden_states is not None:
                    encoder_hidden_states = torch.cat([audio_hidden_states, encoder_hidden_states], dim=1)
                else:
                    encoder_hidden_states = audio_hidden_states

        if (labels is not None) and (decoder_input_ids is None and decoder_inputs_embeds is None):
            decoder_input_ids = shift_tokens_right(
                labels, self.config.decoder.pad_token_id, self.config.decoder.bos_token_id
            )

        # Decode
        decoder_outputs: MusicgenMelodyOutputWithPast = self.decoder(
            input_ids=decoder_input_ids,
            attention_mask=decoder_attention_mask,
            encoder_hidden_states=encoder_hidden_states,
            inputs_embeds=decoder_inputs_embeds,
            use_cache=use_cache,
            past_key_values=past_key_values,
            labels=labels,
            **kwargs_decoder,
        )

        return MusicgenMelodyOutputWithPast(
            loss=decoder_outputs.loss,
            logits=decoder_outputs.logits,
            past_key_values=decoder_outputs.past_key_values,
            hidden_states=decoder_outputs.hidden_states,
            attentions=decoder_outputs.attentions,
            encoder_hidden_states=encoder_hidden_states,
        )