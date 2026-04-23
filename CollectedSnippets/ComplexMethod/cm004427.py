def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        attention_mask: torch.BoolTensor | None = None,
        input_values: torch.FloatTensor | None = None,
        padding_mask: torch.BoolTensor | None = None,
        decoder_input_ids: torch.LongTensor | None = None,
        decoder_attention_mask: torch.BoolTensor | None = None,
        encoder_outputs: tuple[torch.FloatTensor] | None = None,
        past_key_values: Cache | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        decoder_inputs_embeds: torch.FloatTensor | None = None,
        labels: torch.LongTensor | None = None,
        use_cache: bool | None = None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> tuple | Seq2SeqLMOutput:
        r"""
        padding_mask (`torch.BoolTensor` of shape `(batch_size, sequence_length)`, *optional*):
            Mask to avoid performing attention on padding token indices. Mask values selected in `[0, 1]`:

            - 1 for tokens that are **not masked**,
            - 0 for tokens that are **masked**.

            [What are attention masks?](../glossary#attention-mask)
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
        labels (`torch.LongTensor` of shape `(batch_size, sequence_length, num_codebooks)`, *optional*):
            Labels for language modeling. Note that the labels **are shifted** inside the model, i.e. you can set
            `labels = input_ids` Indices are selected in `[-100, 0, ..., config.vocab_size]` All labels set to `-100`
            are ignored (masked), the loss is only computed for labels in `[0, ..., config.vocab_size]`

        Examples:
        ```python
        >>> from transformers import AutoProcessor, MusicgenForConditionalGeneration
        >>> import torch

        >>> processor = AutoProcessor.from_pretrained("facebook/musicgen-small")
        >>> model = MusicgenForConditionalGeneration.from_pretrained("facebook/musicgen-small")

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
        >>> logits.shape  # (bsz * num_codebooks, tgt_len, vocab_size)
        torch.Size([8, 1, 2048])
        ```"""
        kwargs_text_encoder = {}
        kwargs_audio_encoder = {}
        kwargs_decoder = {}
        common_kwargs = {}
        for key, value in kwargs.items():
            if key.startswith("text_encoder_"):
                kwargs_text_encoder[key[len("text_encoder_") :]] = value
            elif key.startswith("audio_encoder_"):
                kwargs_audio_encoder[key[len("audio_encoder_") :]] = value
            elif key.startswith("decoder_"):
                kwargs_decoder[key[len("decoder_") :]] = value
            else:
                common_kwargs[key] = value

        if encoder_outputs is None:
            encoder_outputs = self.text_encoder(
                input_ids=input_ids,
                attention_mask=attention_mask,
                inputs_embeds=inputs_embeds,
                **kwargs_text_encoder,
                **common_kwargs,
            )
        elif isinstance(encoder_outputs, tuple):
            encoder_outputs = BaseModelOutput(*encoder_outputs)

        encoder_hidden_states = encoder_outputs[0]

        # optionally project encoder_hidden_states
        if (
            self.text_encoder.config.hidden_size != self.decoder.config.hidden_size
            and self.decoder.config.cross_attention_hidden_size is None
        ):
            encoder_hidden_states = self.enc_to_dec_proj(encoder_hidden_states)

        if attention_mask is not None:
            encoder_hidden_states = encoder_hidden_states * attention_mask[..., None]

        if (labels is not None) and (decoder_input_ids is None and decoder_inputs_embeds is None):
            decoder_input_ids = shift_tokens_right(
                labels, self.config.decoder.pad_token_id, self.config.decoder.decoder_start_token_id
            )

        elif decoder_input_ids is None and decoder_inputs_embeds is None:
            audio_encoder_outputs = self.audio_encoder(
                input_values=input_values,
                padding_mask=padding_mask,
                **kwargs_audio_encoder,
            )
            audio_codes = audio_encoder_outputs.audio_codes
            frames, bsz, codebooks, seq_len = audio_codes.shape
            if frames != 1:
                raise ValueError(
                    f"Expected 1 frame in the audio code outputs, got {frames} frames. Ensure chunking is "
                    "disabled by setting `chunk_length=None` in the audio encoder."
                )

            if self.config.decoder.audio_channels == 2 and audio_codes.shape[2] == self.decoder.num_codebooks // 2:
                # mono input through encodec that we convert to stereo
                audio_codes = audio_codes.repeat_interleave(2, dim=2)

            decoder_input_ids = audio_codes[0, ...].reshape(bsz * self.decoder.num_codebooks, seq_len)

        # Decode
        decoder_outputs: CausalLMOutputWithCrossAttentions = self.decoder(
            input_ids=decoder_input_ids,
            attention_mask=decoder_attention_mask,
            encoder_hidden_states=encoder_hidden_states,
            encoder_attention_mask=attention_mask,
            inputs_embeds=decoder_inputs_embeds,
            use_cache=use_cache,
            past_key_values=past_key_values,
            labels=labels,
            **kwargs_decoder,
            **common_kwargs,
        )

        return Seq2SeqLMOutput(
            loss=decoder_outputs.loss,
            logits=decoder_outputs.logits,
            past_key_values=decoder_outputs.past_key_values,
            decoder_hidden_states=decoder_outputs.hidden_states,
            decoder_attentions=decoder_outputs.attentions,
            cross_attentions=decoder_outputs.cross_attentions,
            encoder_last_hidden_state=encoder_outputs.last_hidden_state,
            encoder_hidden_states=encoder_outputs.hidden_states,
            encoder_attentions=encoder_outputs.attentions,
        )