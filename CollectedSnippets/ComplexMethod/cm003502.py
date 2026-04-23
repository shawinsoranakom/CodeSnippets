def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        attention_mask: torch.BoolTensor | None = None,
        user_input_values: torch.FloatTensor | None = None,
        user_audio_codes: torch.Tensor | None = None,
        moshi_input_values: torch.FloatTensor | None = None,
        moshi_audio_codes: torch.Tensor | None = None,
        past_key_values: Cache | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        text_labels: torch.LongTensor | None = None,
        audio_labels: torch.LongTensor | None = None,
        use_cache: bool | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple | Seq2SeqLMOutput:
        r"""
        user_input_values (`torch.Tensor `of shape `(batch_size, 1, audio_sequence_length), *optional*):
            The audio waveforms used as audio user prompt for the generation.
        user_audio_codes (`torch.Tensor `of shape `(batch_size, num_codebooks, sequence_length), *optional*):
            The audio codes used as audio user prompt for the generation. Has priority over `user_input_values` and represents the audio "tokens" of `user_input_values` once passed through the audio encoder.
        moshi_input_values (`torch.Tensor `of shape `(batch_size, 1, audio_sequence_length), *optional*):
            The audio waveforms used as audio Moshi prompt for the generation.
        moshi_audio_codes (`torch.Tensor `of shape `(batch_size, num_codebooks, sequence_length), *optional*):
            The audio codes used as audio Moshi prompt for the generation. Has priority over `moshi_input_values` and represents the audio "tokens" of `moshi_input_values` once passed through the audio encoder.
        inputs_embeds (`torch.FloatTensor` of shape `(batch_size, sequence_length, hidden_size)`, *optional*):
            Optionally, instead of passing `input_ids` you can choose to directly pass an embedded
            representation. If `past_key_values` is used, optionally only the last `inputs_embeds` have to be
            input (see `past_key_values`). This is useful if you want more control over how to convert
            `input_ids` indices into associated vectors than the model's internal embedding lookup matrix.

            If `input_ids` and `inputs_embeds` are both unset, `inputs_embeds` takes the value
            of `inputs_embeds`.
        text_labels (`torch.LongTensor` of shape `(batch_size, sequence_length)`, *optional*):
            Labels for text language modeling. Note that the labels **are shifted** inside the model, i.e. you can set
            `labels = input_ids` Indices are selected in `[-100, 0, ..., config.vocab_size]` All labels set to `-100`
            are ignored (masked), the loss is only computed for labels in `[0, ..., config.vocab_size]`
        audio_labels (`torch.LongTensor` of shape `(batch_size, num_codebooks, sequence_length)`, *optional*):
            Labels for language modeling. Note that the labels **are shifted** inside the model, i.e. you can set
            `labels = input_ids` Indices are selected in `[-100, 0, ..., config.vocab_size]` All labels set to `-100`
            are ignored (masked), the loss is only computed for labels in `[0, ..., config.audio_vocab_size]`

        Examples:
        ```python
        >>> from transformers import MoshiForConditionalGeneration
        >>> import torch

        >>> model = MoshiForConditionalGeneration.from_pretrained("kmhf/hf-moshiko")
        >>> inputs = moshi.get_unconditional_inputs()

        >>> logits = model(**inputs, ).logits
        >>> logits.shape  # (bsz, seq_len, text_vocab_size)
        torch.Size([1, 1, 32000])
        ```"""
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        kwargs_audio_encoder = {
            argument[len("audio_encoder_")]: value
            for argument, value in kwargs.items()
            if argument.startswith("audio_encoder_")
        }

        kwargs_decoder = {
            argument[len("decoder_") :]: value for argument, value in kwargs.items() if argument.startswith("decoder_")
        }

        kwargs_depth_decoder = {
            argument[len("depth_decoder_") :]: value
            for argument, value in kwargs.items()
            if argument.startswith("depth_decoder_")
        }

        # If inputs_embeds is provided, it has the priority over input_ids and audio_codes, which won't be used
        if inputs_embeds is None:
            if user_input_values is not None and user_audio_codes is None:
                user_audio_codes = self.audio_encoder.encode(
                    user_input_values, num_quantizers=self.num_codebooks, **kwargs_audio_encoder
                )[0]

            if moshi_input_values is not None and moshi_audio_codes is None:
                moshi_audio_codes = self.audio_encoder.encode(
                    moshi_input_values, num_quantizers=self.num_codebooks, **kwargs_audio_encoder
                )[0]

            audio_codes = torch.cat([moshi_audio_codes, user_audio_codes], dim=1)

            if input_ids is None and audio_codes is None:
                raise ValueError(
                    "You must provide at least one of `input_ids`, `inputs_embeds`, `input_values` and `audio_codes`."
                )

            if input_ids is not None:
                inputs_embeds = self.decoder.model.embed_tokens(input_ids)

            if audio_codes is not None:
                audio_inputs_embeds = sum(
                    self.embed_tokens[codebook](audio_codes[:, codebook]) for codebook in range(audio_codes.shape[1])
                )
                inputs_embeds = (
                    audio_inputs_embeds
                    if inputs_embeds is None
                    else audio_inputs_embeds + inputs_embeds.to(audio_inputs_embeds.device)
                )

        # Decode
        decoder_outputs = self.decoder(
            attention_mask=attention_mask,
            inputs_embeds=inputs_embeds,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            use_cache=use_cache,
            past_key_values=past_key_values,
            return_dict=True,
            labels=text_labels,
            **kwargs_decoder,
        )

        decoder_last_hidden_state = decoder_outputs.last_hidden_state

        depth_decoder_outputs = None
        final_loss = decoder_outputs.loss
        if text_labels is not None and audio_labels is not None:
            # To use depth decoder forward here, we actually need oracle input ids since we're supposed to pass the true input ids

            audio_labels = self.build_delay_pattern_mask(
                audio_labels,
                bos_token_id=self.config.audio_vocab_size,
                pad_token_id=self.config.audio_vocab_size,
                max_length=audio_labels.shape[-1] + 1,
            )[0]

            # (batch_size, sequence_length) -> (batch_size * sequence_length, 1)
            text_labels = text_labels.view(-1, 1)

            # (batch_size, num_codebooks, sequence_length) -> (batch_size * sequence_length, num_codebooks)
            audio_labels = audio_labels.transpose(1, 2).reshape(-1, audio_labels.shape[1])

            depth_input_ids = torch.cat([text_labels, audio_labels], dim=1)
            # keep the last codebook out of input_ids
            depth_input_ids = depth_input_ids[:, :-1]

            # (batch_size, sequence_length, dim) -> (batch_size * sequence_length, 1, dim)
            decoder_last_hidden_state = decoder_last_hidden_state.view(-1, 1, decoder_last_hidden_state.shape[-1])

            depth_decoder_outputs = self.depth_decoder(
                last_hidden_state=decoder_last_hidden_state,
                input_ids=depth_input_ids,
                attention_mask=attention_mask,
                labels=audio_labels,
                **kwargs_depth_decoder,
            )

            final_loss += depth_decoder_outputs.loss

        if not return_dict:
            outputs = decoder_outputs.to_tuple()
            if depth_decoder_outputs is not None:
                outputs += depth_decoder_outputs.to_tuple()
            return outputs

        return MoshiConditionalGenerationOutputWithPast(
            loss=decoder_outputs.loss,
            logits=decoder_outputs.logits,
            last_hidden_state=decoder_last_hidden_state,
            past_key_values=decoder_outputs.past_key_values,
            hidden_states=decoder_outputs.hidden_states,
            attentions=decoder_outputs.attentions,
            depth_loss=None if depth_decoder_outputs is None else depth_decoder_outputs.loss,
            audio_logits=None if depth_decoder_outputs is None else depth_decoder_outputs.logits,
            depth_past_key_values=None if decoder_outputs is None else decoder_outputs.past_key_values,
            depth_hidden_states=None if decoder_outputs is None else decoder_outputs.hidden_states,
            depth_attentions=None if decoder_outputs is None else decoder_outputs.attentions,
        )