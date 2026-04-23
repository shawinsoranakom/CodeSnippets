def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        attention_mask: torch.LongTensor | None = None,
        decoder_input_ids: torch.LongTensor | None = None,
        decoder_position_ids: torch.LongTensor | None = None,
        decoder_attention_mask: torch.LongTensor | None = None,
        encoder_outputs: BaseModelOutput | tuple | None = None,
        past_key_values: EncoderDecoderCache | None = None,
        use_cache: bool | None = None,
        **kwargs,
    ) -> tuple | Seq2SeqModelOutput:
        r"""
        decoder_input_ids (`torch.LongTensor` of shape `(batch_size * num_codebooks, target_sequence_length)
        or (batch_size, target_sequence_length, num_codebooks)`, *optional*):
            1. (batch_size * num_codebooks, target_sequence_length): corresponds to the general use case where
            the audio input codebooks are flattened into the batch dimension. This also aligns with the flat-
            tened audio logits which are used to calculate the loss.

            2. (batch_size, sequence_length, num_codebooks): corresponds to the internally used shape of
            Dia to calculate embeddings and subsequent steps more efficiently.

            If no `decoder_input_ids` are provided, it will create a tensor of `bos_token_id` with shape
            `(batch_size, 1, num_codebooks)`. Indices can be obtained using the [`DiaProcessor`]. See
            [`DiaProcessor.__call__`] for more details.

            [What are decoder input IDs?](../glossary#decoder-input-ids)
        decoder_position_ids (`torch.LongTensor` of shape `(batch_size, target_sequence_length)`):
            Indices of positions of each input sequence tokens in the position embeddings.
            Used to calculate the position embeddings up to `config.decoder_config.max_position_embeddings`.

            [What are position IDs?](../glossary#position-ids)
        """

        if input_ids is None and encoder_outputs is None:
            raise ValueError(
                "You should either provide text ids or the cached text encodings. Neither has been found."
            )

        if self.is_gradient_checkpointing and self.training:
            if use_cache:
                logger.warning_once(
                    "`use_cache=True` is incompatible with gradient checkpointing. Setting `use_cache=False`..."
                )
                use_cache = False

        if use_cache and past_key_values is None:
            past_key_values = EncoderDecoderCache(DynamicCache(config=self.config), DynamicCache(config=self.config))

        if encoder_outputs is None:
            encoder_outputs = self.encoder(
                input_ids=input_ids,
                attention_mask=attention_mask,
                **kwargs,
            )
        # If the user passed a tuple for encoder_outputs, we wrap it in a BaseModelOutput
        elif not isinstance(encoder_outputs, BaseModelOutput):
            encoder_outputs = BaseModelOutput(
                last_hidden_state=encoder_outputs[0],
                hidden_states=encoder_outputs[1] if len(encoder_outputs) > 1 else None,
                attentions=encoder_outputs[2] if len(encoder_outputs) > 2 else None,
            )

        # On default we initialize the decoder with bos tokens if nothing has been provided
        bsz, seq_len, channels = (encoder_outputs[0].shape[0], -1, self.config.decoder_config.num_channels)
        if decoder_input_ids is None:
            decoder_input_ids = torch.full(
                size=(bsz, 1, channels), fill_value=self.config.decoder_config.bos_token_id, device=self.device
            )
        # Ensure 3D
        if decoder_input_ids.ndim == 2:
            decoder_input_ids = decoder_input_ids.reshape(bsz, channels, seq_len).transpose(1, 2)

        decoder_outputs = self.decoder(
            input_ids=decoder_input_ids,
            position_ids=decoder_position_ids,
            attention_mask=decoder_attention_mask,
            encoder_hidden_states=encoder_outputs[0],
            encoder_attention_mask=attention_mask,
            past_key_values=past_key_values,
            use_cache=use_cache,
            **kwargs,
        )

        return Seq2SeqModelOutput(
            last_hidden_state=decoder_outputs.last_hidden_state,
            past_key_values=decoder_outputs.past_key_values,
            decoder_hidden_states=decoder_outputs.hidden_states,
            decoder_attentions=decoder_outputs.attentions,
            cross_attentions=decoder_outputs.cross_attentions,
            encoder_last_hidden_state=encoder_outputs[0],
            encoder_hidden_states=encoder_outputs.hidden_states,
            encoder_attentions=encoder_outputs.attentions,
        )