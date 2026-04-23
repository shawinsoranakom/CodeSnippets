def generate(
        self,
        input_ids: torch.Tensor | None = None,
        return_intermediate_token_ids: bool | None = None,
        tgt_lang: str | None = None,
        spkr_id: int | None = 0,
        **kwargs,
    ) -> torch.Tensor | SeamlessM4TGenerationOutput:
        """
        Generates translated audio waveforms.

        <Tip>

        This method successively calls the `.generate` function of two different sub-models. You can specify keyword
        arguments at two different levels: general arguments that will be passed to both models, or prefixed arguments
        that will be passed to one of them.

        For example, calling `.generate(input_ids, num_beams=4, speech_do_sample=True)` will successively perform
        beam-search decoding on the text model, and multinomial beam-search sampling on the speech model.

        For an overview of generation strategies and code examples, check out the [following
        guide](./generation_strategies).

        </Tip>

        Args:
            input_ids (`torch.LongTensor` of shape `(batch_size, sequence_length)`):
                Indices of input sequence tokens in the vocabulary.

                Indices can be obtained using [`SeamlessM4TTokenizer`] or [`SeamlessM4TProcessor`]. See
                [`PreTrainedTokenizer.encode`] and [`PreTrainedTokenizer.__call__`] for details.

                [What are input IDs?](../glossary#input-ids)
            return_intermediate_token_ids (`bool`, *optional*):
                If `True`, also returns the intermediate generated text and unit tokens. Set to `True` if you also want
                to get translated text alongside the audio.
            tgt_lang (`str`, *optional*):
                The language to use as target language for translation.
            spkr_id (`int`, *optional*, defaults to 0):
                The id of the speaker used for speech synthesis. Must be lower than `config.vocoder_num_spkrs`.
            kwargs (*optional*):
                Remaining dictionary of keyword arguments that will be passed to [`GenerationMixin.generate`]. Keyword
                arguments are of two types:

                    - Without a prefix, they will be entered as `**kwargs` for the `generate` method of each sub-model,
                    except for `decoder_input_ids` which will only be passed through the text components.
                    - With a *text_* or *speech_* prefix, they will be input for the `generate` method of the
                    text model and speech model respectively. It has the priority over the keywords without a prefix.

                    This means you can, for example, specify a generation strategy for one generation but not for the
                    other.


        Returns:
            `Union[SeamlessM4TGenerationOutput, tuple[Tensor]]`:
            - If `return_intermediate_token_ids`, returns [`SeamlessM4TGenerationOutput`].
            - If not `return_intermediate_token_ids`, returns a tuple composed of waveforms of shape `(batch_size,
              sequence_length)` and `waveform_lengths` which gives the length of each sample.
        """
        batch_size = len(input_ids) if input_ids is not None else len(kwargs.get("inputs_embeds"))

        if tgt_lang is None:
            raise ValueError("You must specify a `tgt_lang` to generate translated speech.")
        else:
            # also accept __xxx__
            tgt_lang = tgt_lang.replace("__", "")
            for key in ["text_decoder_lang_to_code_id", "t2u_lang_code_to_id", "vocoder_lang_code_to_id"]:
                lang_code_to_id = getattr(self.generation_config, key, None)
                if lang_code_to_id is None:
                    raise ValueError(
                        f"""This model generation config doesn't have a `{key}` key which maps the target language
                        to the right token id. Make sure to load the right generation config."""
                    )
                elif tgt_lang not in lang_code_to_id:
                    raise ValueError(
                        f"""`tgt_lang={tgt_lang}` is not supported by this model.
                    Please specify a `tgt_lang` in {",".join(lang_code_to_id.keys())}. Note that SeamlessM4T supports
                    more languages for text translation than for speech synthesis."""
                    )

        kwargs_text, kwargs_speech = format_speech_generation_kwargs(kwargs)
        kwargs_text["output_hidden_states"] = True
        kwargs_text["return_dict_in_generate"] = True
        kwargs_text["output_scores"] = True

        text_decoder_input_ids = kwargs_text.get("decoder_input_ids")

        # overwrite text_decoder_input_ids if tgt_lang is passed. The latter gets priority over decoder_input_ids.
        text_tgt_lang_id = self.generation_config.text_decoder_lang_to_code_id.get(tgt_lang)
        text_decoder_input_ids = torch.tensor([[text_tgt_lang_id]] * batch_size, device=self.device)

        kwargs_text["decoder_input_ids"] = text_decoder_input_ids

        # first generation
        text_generation_output = super().generate(input_ids, **kwargs_text)
        sequences = text_generation_output.sequences

        # prepare second generation
        num_return_sequences = len(sequences) // batch_size
        attention_mask = kwargs_speech.get("attention_mask", kwargs_text.get("attention_mask", None))

        encoder_hidden_states = text_generation_output.encoder_hidden_states[-1]

        # take care of num_return_sequences
        # take most probable hidden states per batch of return_sequences
        # (batch_size*num_return_sequences, ...) -> (batch_size,...)
        if num_return_sequences > 1:
            idx_most_probable_sequences_per_batch = text_generation_output.sequences_scores.view(batch_size, -1)
            idx_most_probable_sequences_per_batch = idx_most_probable_sequences_per_batch.argmax(-1)
            idx_most_probable_sequences_per_batch = (
                idx_most_probable_sequences_per_batch
                + torch.arange(batch_size, device=self.device) * num_return_sequences
            )
            sequences = sequences[idx_most_probable_sequences_per_batch]

        # get decoder last hidden state - must do a pass through the text decoder
        t2u_input_embeds = self.text_decoder(
            input_ids=sequences,
            encoder_hidden_states=encoder_hidden_states,
            encoder_attention_mask=attention_mask,
        ).last_hidden_state

        pad_token_id = self.generation_config.pad_token_id

        # Compute new attention mask
        seq_lens = (sequences != pad_token_id).int().sum(1)
        t2u_model_attention_mask = _compute_new_attention_mask(t2u_input_embeds, seq_lens)
        kwargs_speech["attention_mask"] = t2u_model_attention_mask

        # Compute t2u decoder_input_ids
        t2u_decoder_input_ids = kwargs_speech.get("decoder_input_ids")
        t2u_tgt_lang_id = self.generation_config.t2u_lang_code_to_id.get(tgt_lang)
        t2u_decoder_input_ids = torch.tensor(
            [[self.config.t2u_eos_token_id, t2u_tgt_lang_id]] * batch_size, device=self.device
        )
        kwargs_speech["decoder_input_ids"] = t2u_decoder_input_ids
        # second generation
        unit_ids = self.t2u_model.generate(inputs_embeds=t2u_input_embeds, **kwargs_speech)
        output_unit_ids = unit_ids.detach().clone()

        # get rid of t2u_decoder_input_ids
        unit_ids = unit_ids[:, kwargs_speech["decoder_input_ids"].shape[1] :]
        # replace eos per pad
        unit_ids[unit_ids == self.config.t2u_eos_token_id] = self.config.t2u_pad_token_id
        # offset of control symbols
        unit_ids = torch.where(
            unit_ids == self.config.t2u_pad_token_id, unit_ids, unit_ids - self.config.vocoder_offset
        )

        vocoder_tgt_lang_id = self.generation_config.vocoder_lang_code_to_id.get(tgt_lang)
        vocoder_tgt_lang_id = torch.tensor([[vocoder_tgt_lang_id]] * len(unit_ids), device=self.device)

        spkr_id = torch.tensor([[spkr_id]] * len(unit_ids), device=self.device)

        waveform, waveform_lengths = self.vocoder(input_ids=unit_ids, spkr_id=spkr_id, lang_id=vocoder_tgt_lang_id)

        if return_intermediate_token_ids:
            return SeamlessM4TGenerationOutput(
                waveform=waveform,
                waveform_lengths=waveform_lengths,
                sequences=sequences,
                unit_sequences=output_unit_ids,
            )

        return waveform, waveform_lengths