def generate(
        self,
        input_ids: torch.Tensor | None = None,
        input_features: torch.Tensor | None = None,
        return_intermediate_token_ids: bool | None = None,
        tgt_lang: str | None = None,
        speaker_id: int | None = 0,
        generate_speech: bool | None = True,
        **kwargs,
    ) -> torch.Tensor | SeamlessM4Tv2GenerationOutput:
        """
        Generates translated token ids and/or translated audio waveforms.

        <Tip>

        This method successively calls the `.generate` function of two different sub-models. You can specify keyword
        arguments at two different levels: general arguments that will be passed to both models, or prefixed arguments
        that will be passed to one of them.

        For example, calling `.generate(input_ids=input_ids, num_beams=4, speech_do_sample=True)` will successively
        perform beam-search decoding on the text model, and multinomial beam-search sampling on the speech model.

        For an overview of generation strategies and code examples, check out the [following
        guide](./generation_strategies).

        </Tip>


        Args:
            input_ids (`torch.LongTensor` of shape `(batch_size, sequence_length)`, *optional*):
                Indices of input sequence tokens in the vocabulary.

                Indices can be obtained using [`SeamlessM4TTokenizer`] or [`SeamlessM4TProcessor`]. See
                [`PreTrainedTokenizer.encode`] and [`PreTrainedTokenizer.__call__`] for details.

                [What are input IDs?](../glossary#input-ids)
            input_features (`torch.FloatTensor` of shape `(batch_size, sequence_length, num_banks)`, *optional*):
                Input audio features. This should be returned by the [`SeamlessM4TFeatureExtractor`] class or the
                [`SeamlessM4TProcessor`] class. See [`SeamlessM4TFeatureExtractor.__call__`] for details.
            return_intermediate_token_ids (`bool`, *optional*):
                If `True`, also returns the intermediate generated text and unit tokens. Set to `True` if you also want
                to get translated text alongside the audio.
                Note that if `generate_speech=False`, this parameter will be ignored and
                the text tokens are returned.
            tgt_lang (`str`, *optional*):
                The language to use as target language for translation.
            speaker_id (`int`, *optional*, defaults to 0):
                The id of the speaker used for speech synthesis. Must be lower than `config.vocoder_num_spkrs`.
            generate_speech (`bool`, *optional*, defaults to `True`):
                If `False`, will only returns the text tokens and won't generate speech.

            kwargs (*optional*):
                Remaining dictioy of keyword arguments that will be passed to [`GenerationMixin.generate`]. Keyword
                arguments are of two types:

                    - Without a prefix, they will be entered as `**kwargs` for the `generate` method of each sub-model,
                    except for `decoder_input_ids` which will only be passed through the text components.
                    - With a *text_* or *speech_* prefix, they will be input for the `generate` method of the
                    text model and speech model respectively. It has the priority over the keywords without a prefix.

                    This means you can, for example, specify a generation strategy for one generation but not for the
                    other.

        Returns:
            `Union[SeamlessM4Tv2GenerationOutput, tuple[Tensor], ModelOutput]`:
            - If `generate_speech` and `return_intermediate_token_ids`, returns [`SeamlessM4Tv2GenerationOutput`].
            - If `generate_speech` and not `return_intermediate_token_ids`, returns a tuple composed of waveforms of
              shape `(batch_size, sequence_length)` and `waveform_lengths` which gives the length of each sample.
            - If `generate_speech=False`, it will returns `ModelOutput`.
        """
        if input_ids is None and input_features is None and kwargs.get("inputs_embeds") is None:
            raise ValueError(
                "`input_ids`,`input_features` and `inputs_embeds` are all empty. Make sure at least one of them is not."
            )

        if generate_speech and tgt_lang is None:
            raise ValueError("You must specify a `tgt_lang` to generate translated speech.")

        if tgt_lang is not None:
            # also accept __xxx__
            tgt_lang = tgt_lang.replace("__", "")
            if generate_speech:
                keys_to_check = ["text_decoder_lang_to_code_id", "t2u_lang_code_to_id", "vocoder_lang_code_to_id"]
            else:
                keys_to_check = ["text_decoder_lang_to_code_id"]
            for key in keys_to_check:
                lang_code_to_id = getattr(self.generation_config, key, None)
                if lang_code_to_id is None:
                    raise ValueError(
                        f"""This model generation config doesn't have a `{key}` key which maps the target language
                        to the right token id. Make sure to load the right generation config."""
                    )
                elif tgt_lang not in lang_code_to_id:
                    raise ValueError(
                        f"""`tgt_lang={tgt_lang}` is not supported by this model.
                    Please specify a `tgt_lang` in {",".join(lang_code_to_id.keys())}. Note that SeamlessM4Tv2 supports
                    more languages for text translation than for speech synthesis."""
                    )

        batch_size = (
            len(input_features)
            if input_features is not None
            else (len(input_ids) if input_ids is not None else len(kwargs.get("inputs_embeds")))
        )

        kwargs_text, kwargs_speech = format_speech_generation_kwargs(kwargs)
        kwargs_text["output_hidden_states"] = True
        kwargs_text["return_dict_in_generate"] = True
        kwargs_text["output_scores"] = True

        text_decoder_input_ids = kwargs_text.get("decoder_input_ids")
        # overwrite text_decoder_input_ids if tgt_lang is passed. The latter gets priority over decoder_input_ids.
        if tgt_lang is not None:
            # tgt_lang gets priority over decoder input ids
            text_tgt_lang_id = self.generation_config.text_decoder_lang_to_code_id.get(tgt_lang)
            text_decoder_input_ids = torch.tensor([[text_tgt_lang_id]] * batch_size, device=self.device)

        kwargs_text["decoder_input_ids"] = text_decoder_input_ids

        # first generation
        if input_features is not None:
            self.set_modality("speech")
            if input_ids is not None:
                logger.warning(
                    "`input_features` and `input_ids` are both non empty. `input_features` will be used in priority "
                    "through the speech encoder. Make sure `input_features=None` if you want to use the text encoder."
                )
            text_generation_output = super().generate(input_features=input_features, **kwargs_text)
        else:
            self.set_modality("text")
            text_generation_output = super().generate(input_ids=input_ids, input_features=None, **kwargs_text)
        sequences = text_generation_output.sequences

        if not generate_speech:
            return text_generation_output

        # prepare second generation
        num_return_sequences = len(sequences) // batch_size
        attention_mask = kwargs_speech.get("attention_mask", kwargs_text.get("attention_mask", None))

        # get encoder last hidden states
        if self.current_modality == "speech":
            # get last_hidden_state from encoder - must do a pass through the speech encoder
            encoder_hidden_states = self.speech_encoder(
                input_features=input_features, attention_mask=attention_mask
            ).last_hidden_state

            # input modality = speech so new attention mask for the decoder
            if attention_mask is not None:
                sub_sampled_lengths = self._compute_sub_sample_lengths_from_attention_mask(attention_mask).to(
                    encoder_hidden_states.device
                )
                attention_mask = _compute_new_attention_mask(
                    hidden_states=encoder_hidden_states, seq_lens=sub_sampled_lengths
                )
        else:
            encoder_hidden_states = text_generation_output.encoder_hidden_states[-1]

        if attention_mask is not None:
            # repeat attention mask alongside batch dimension
            attention_mask = torch.repeat_interleave(attention_mask, num_return_sequences, dim=0)

        # repeat attention mask alongside batch dimension
        encoder_hidden_states = torch.repeat_interleave(encoder_hidden_states, num_return_sequences, dim=0)

        # get decoder last hidden state - must do a pass through the text decoder
        t2u_input_embeds = self.text_decoder(
            input_ids=sequences[:, :-1],  # Manually trim the final EOS token
            encoder_hidden_states=encoder_hidden_states,
            encoder_attention_mask=attention_mask,
        ).last_hidden_state

        pad_token_id = self.generation_config.pad_token_id

        # Compute new attention mask
        seq_lens = (sequences[:, :-1] != pad_token_id).int().sum(1)
        t2u_model_attention_mask = _compute_new_attention_mask(t2u_input_embeds, seq_lens)
        kwargs_speech["attention_mask"] = t2u_model_attention_mask

        # REMOVE EOS and lang_id
        t2u_input_ids = sequences[:, 2:-1]
        # replace every other EOS
        t2u_input_ids = torch.masked_fill(
            t2u_input_ids, t2u_input_ids == self.generation_config.eos_token_id, pad_token_id
        )

        # compute t2u_char_input_ids
        t2u_subwords = self._indices_to_subwords(t2u_input_ids)
        t2u_char_count_per_id = self._count_character_length_in_subword(
            t2u_input_ids, t2u_subwords, pad_token_id=pad_token_id
        )

        # Add pads for lang, EOS tokens as per NLLB "source" tokenizer mode.
        pad_zero = t2u_char_count_per_id.new_zeros((t2u_char_count_per_id.shape[0], 1))
        t2u_char_count_per_id = torch.cat([pad_zero, t2u_char_count_per_id, pad_zero], dim=1)
        t2u_char_input_ids = self._get_char_input_ids(
            t2u_input_ids, t2u_subwords, t2u_char_count_per_id, pad_token_id=pad_token_id
        )

        # second pass
        t2u_output = self.t2u_model(
            inputs_embeds=t2u_input_embeds,
            char_input_ids=t2u_char_input_ids,
            char_count_per_id=t2u_char_count_per_id,
            **kwargs_speech,
        )

        t2u_logits = t2u_output[0]
        padding_mask = t2u_output[1].bool()

        # The text-to-unit model is non auto-regressive. We keep the ability to use sampling with temperature
        temperature = kwargs_speech.get("temperature", None)
        if (temperature is None or temperature == 1.0) or not kwargs_speech.get("do_sample", False):
            unit_ids = t2u_logits.argmax(dim=-1)
        else:
            t2u_logits = t2u_logits / temperature
            # apply softmax
            probs = nn.functional.softmax(t2u_logits, dim=-1)
            # reshape to 2D: (batch_size, seq_len, t2u_vocab_size) -> (batch_size*seq_len, t2u_vocab_size)
            probs = probs.reshape((-1, probs.shape[2]))
            # multinomial then reshape : (batch_size*seq_len)-> (batch_size,seq_len)
            unit_ids = torch.multinomial(probs, num_samples=1).view(t2u_logits.shape[0], -1)

        output_unit_ids = unit_ids.detach().clone()

        replace_mask = (unit_ids == self.config.t2u_eos_token_id) | (~padding_mask)
        # replace eos per pad
        unit_ids = unit_ids.masked_fill(replace_mask, self.config.t2u_pad_token_id)

        # offset of control symbols
        unit_ids = torch.where(
            unit_ids == self.config.t2u_pad_token_id, unit_ids, unit_ids - self.config.vocoder_offset
        )

        vocoder_tgt_lang_id = self.generation_config.vocoder_lang_code_to_id.get(tgt_lang)
        vocoder_tgt_lang_id = torch.tensor([[vocoder_tgt_lang_id]] * len(unit_ids), device=self.device)

        speaker_id = torch.tensor([[speaker_id]] * len(unit_ids), device=self.device)

        waveform, waveform_lengths = self.vocoder(
            input_ids=unit_ids, speaker_id=speaker_id, lang_id=vocoder_tgt_lang_id
        )

        if return_intermediate_token_ids:
            return SeamlessM4Tv2GenerationOutput(
                waveform=waveform,
                waveform_lengths=waveform_lengths,
                sequences=sequences,
                unit_sequences=output_unit_ids,
            )

        return waveform, waveform_lengths