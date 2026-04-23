def generate(
        self,
        input_ids: torch.LongTensor | None = None,
        user_input_values: torch.FloatTensor | None = None,
        user_audio_codes: torch.Tensor | None = None,
        moshi_input_values: torch.FloatTensor | None = None,
        moshi_audio_codes: torch.Tensor | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        return_audio_waveforms: bool | None = True,
        return_audio_codes: bool | None = None,
        concat_unconditional_inputs: bool | None = True,
        **kwargs,
    ) -> torch.LongTensor:
        """
        Generates sequences of text token ids and audio tokens ids.

        Parameters:
            input_ids (`torch.Tensor `of shape `(batch_size, sequence_length), *optional*):
                The sequence used as a text prompt for the generation.
            user_input_values (`torch.Tensor `of shape `(batch_size, 1, audio_sequence_length), *optional*):
                The audio waveforms used as audio user prompt for the generation.
            user_audio_codes (`torch.Tensor `of shape `(batch_size, num_codebooks, sequence_length), *optional*):
                The audio codes used as audio user prompt for the generation. Has priority over `user_input_values` and represents the audio "tokens" of `user_input_values` once passed through the audio encoder.
            moshi_input_values (`torch.Tensor `of shape `(batch_size, 1, audio_sequence_length), *optional*):
                The audio waveforms used as audio Moshi prompt for the generation.
            moshi_audio_codes (`torch.Tensor `of shape `(batch_size, num_codebooks, sequence_length), *optional*):
                The audio codes used as audio Moshi prompt for the generation. Has priority over `moshi_input_values` and represents the audio "tokens" of `moshi_input_values` once passed through the audio encoder.
            inputs_embeds (`torch.FloatTensor` of shape `(batch_size, sequence_length, hidden_size)`, *optional*):
                Optionally, instead of passing `input_ids` and the audio inputs you can choose to directly pass an embedded representation. This
                is useful if you want more control over how to convert the inputs into associated vectors than the
                model's internal embedding lookup matrix.
            return_audio_waveforms (`bool`, *optional*, defaults to `True`):
                If `False`, won't generate the audio waveforms.
            return_audio_codes (`bool`, *optional*):
                If `True`, will also returns the generated audio codes, i.e the intermediate audio "tokens" which transforms to `audio_sequences` once passed through the audio decoder.
            concat_unconditional_inputs (`bool`, *optional*, defaults to `True`):
                If `False`, won't concatenate initial audio and text tokens.
            kwargs (`dict[str, Any]`, *optional*):
                Remaining dictionary of keyword arguments that are passed to the `generate` method. Refers to the
                original [`generate` docstrings](https://huggingface.co/docs/transformers/main/en/main_classes/text_generation#transformers.GenerationMixin.generate)
                for more information on how to use them.
                Note that keywords with a *depth_* prefix will be input for the `generate` method of the
                depth decoder. Otherwise, the latter will use its default generation config.
        Return:
            [`MoshiConditionalGenerationGenerateOutput`]
        """
        # multiple generate -> need to create/update device map
        if hasattr(self, "hf_device_map") and not hasattr(self.depth_decoder, "hf_device_map"):
            self.depth_decoder.hf_device_map = {}
            if "" in self.hf_device_map:
                self.depth_decoder.hf_device_map = self.hf_device_map
            else:
                main_device = [d for d in self.hf_device_map.values() if d not in ["cpu", "disk"]][0]
                self.depth_decoder.hf_device_map = {
                    key[len("depth_decoder") :]: main_device if value in ["cpu", "disk"] else value
                    for key, value in self.hf_device_map.items()
                    if key.startswith("depth_decoder")
                }
            # need to remove depth_decoder from the top device_map so that we assign correctly the device for each layer idx in the cache
            self.hf_device_map = {
                key: value for key, value in self.hf_device_map.items() if not key.startswith("depth_decoder")
            }
        # retrieve depth decoder kwargs
        depth_decoder_kwargs_keys = {argument for argument in kwargs if argument.startswith("depth_decoder_")}
        kwargs_depth_decoder = {
            argument[len("depth_decoder_") :]: kwargs.pop(argument) for argument in depth_decoder_kwargs_keys
        }

        # needs to prepare generation config, even though it'll be done again in `generate`
        generation_config, kwargs = self._prepare_generation_config(kwargs.pop("generation_config", None), **kwargs)

        input_ids, user_audio_codes, moshi_audio_codes, concat_unconditional_inputs = (
            self._check_and_maybe_initialize_inputs(
                input_ids=input_ids,
                user_input_values=user_input_values,
                user_audio_codes=user_audio_codes,
                moshi_input_values=moshi_input_values,
                moshi_audio_codes=moshi_audio_codes,
                inputs_embeds=inputs_embeds,
                concat_unconditional_inputs=concat_unconditional_inputs,
            )
        )

        inputs = inputs_embeds if input_ids is None else input_ids

        input_ids_length = inputs.shape[-1] + 1 if concat_unconditional_inputs else inputs.shape[-1]
        has_default_max_length = kwargs.get("max_length") is None and generation_config.max_length is not None
        has_default_min_length = kwargs.get("min_length") is None and generation_config.min_length is not None
        generation_config = self._prepare_generated_length(
            generation_config=generation_config,
            has_default_max_length=has_default_max_length,
            has_default_min_length=has_default_min_length,
            model_input_name="inputs_embeds" if input_ids is None else "input_ids",
            inputs_tensor=inputs,
            input_ids_length=input_ids_length,
        )

        # retrieve depth decoder generation config if it exists
        if hasattr(generation_config, "depth_decoder_config"):
            depth_decoder_generation_config = generation_config.depth_decoder_config
        else:
            # we need to control the number of tokens generated by the depth decoder
            depth_decoder_generation_config = {
                "min_length": self.num_codebooks + 1,
                "max_length": self.num_codebooks + 1,
                "cache_implementation": "static",
            }
        # update kwargs_depth_decoder: kwargs_depth_decoder have priority over depth_decoder_generation_config
        depth_decoder_generation_config.update(kwargs_depth_decoder)
        kwargs_depth_decoder = depth_decoder_generation_config

        attention_mask = kwargs.pop("attention_mask", None)
        if attention_mask is None:
            attention_mask = self._prepare_attention_mask_for_generation(
                input_ids=input_ids,
                generation_config=generation_config,
                kwargs=kwargs,
            )
        (
            inputs_embeds,
            input_ids,
            user_audio_codes,
            moshi_audio_codes,
            user_delay_pattern_mask,
            moshi_delay_pattern_mask,
            attention_mask,
        ) = self._prepare_inputs_embeds_for_generation(
            input_ids=input_ids,
            user_input_values=user_input_values,
            user_audio_codes=user_audio_codes,
            moshi_input_values=moshi_input_values,
            moshi_audio_codes=moshi_audio_codes,
            inputs_embeds=inputs_embeds,
            attention_mask=attention_mask,
            generation_config=generation_config,
            apply_delay_pattern_mask=True,
            concat_unconditional_inputs=concat_unconditional_inputs,
        )

        # create blank user inputs - moshi needs a constant stream of user inputs
        blank_input_values = torch.zeros(
            (inputs_embeds.shape[0], 1, int(self.config.sampling_rate / self.config.audio_encoder_config.frame_rate)),
            dtype=self.dtype,
            device=self.device,
        )
        blank_user_audio_codes = self.audio_encoder.encode(blank_input_values, num_quantizers=self.num_codebooks)[0]

        # set delay pattern mask for the rest of the generation
        kwargs["user_delay_pattern_mask"] = (
            user_delay_pattern_mask if user_delay_pattern_mask is not None else kwargs.get("user_delay_pattern_mask")
        )
        kwargs["moshi_delay_pattern_mask"] = (
            moshi_delay_pattern_mask
            if moshi_delay_pattern_mask is not None
            else kwargs.get("moshi_delay_pattern_mask")
        )

        self.generated_audio_codes = torch.repeat_interleave(
            moshi_audio_codes, max(generation_config.num_beams, generation_config.num_return_sequences), dim=0
        )

        return_dict_in_generate = generation_config.num_beams > 1 or generation_config.return_dict_in_generate
        output_scores = generation_config.num_beams > 1 or generation_config.output_scores
        outputs = super().generate(
            inputs_embeds=inputs_embeds,
            input_ids=input_ids,
            generation_config=generation_config,
            blank_user_audio_codes=blank_user_audio_codes,
            kwargs_depth_decoder=kwargs_depth_decoder,
            return_dict_in_generate=return_dict_in_generate,
            output_scores=output_scores,
            attention_mask=attention_mask,
            **kwargs,
        )

        if not return_audio_waveforms and not return_audio_codes:
            if return_dict_in_generate and not generation_config.return_dict_in_generate:
                return outputs.sequences
            return outputs

        # check if outputs is a dict or tokens
        if not return_dict_in_generate:
            output_text_ids = outputs
        else:
            output_text_ids = outputs.sequences

        if generation_config.num_return_sequences > 1:
            moshi_delay_pattern_mask = torch.repeat_interleave(
                moshi_delay_pattern_mask, generation_config.num_return_sequences, dim=0
            )

        if generation_config.num_beams > 1:
            # we need to reorganize self.last_hidden_states and generated audio codes according to the beam_indices

            # Beam indices are of shape `input_length + number_generated_tokens` but actually starts
            # indexing indices at index 0 instead of index `input_length-1`.
            # We thus discard the last `input_length` indices that are never used.
            beam_indices = outputs.beam_indices[:, : -moshi_audio_codes.shape[-1]]

            generated_audio_codes = self.generated_audio_codes[:, :, moshi_audio_codes.shape[-1] :]

            # we've generated audio tokens `number_generated_tokens-1` times, so we use the corresponding beam indices to
            # retrieve the right audio tokens
            expanded_beam_indices = beam_indices[:, :-1].unsqueeze(1).expand(-1, self.num_codebooks, -1)
            generated_audio_codes = torch.gather(generated_audio_codes, dim=0, index=expanded_beam_indices)

            # now, rebuild generated audio codes, this time with the right beam tracking
            moshi_audio_codes = torch.repeat_interleave(
                moshi_audio_codes, generation_config.num_return_sequences, dim=0
            )
            self.generated_audio_codes = torch.cat((moshi_audio_codes, generated_audio_codes), dim=2)

            # use the last beam indice to retrieve the right self.last_hidden_state
            self.last_hidden_state = torch.index_select(self.last_hidden_state, dim=0, index=beam_indices[:, -1])

        # we need to make a last generation with the latest generated tokens
        last_hidden_state = self.last_hidden_state.view(-1, 1, self.last_hidden_state.shape[-1])

        last_generated_audio_codes = self.depth_decoder.generate(
            last_hidden_state=last_hidden_state,
            input_ids=output_text_ids[:, -1:].view(-1, 1),
            **kwargs_depth_decoder,
        )

        last_generated_audio_codes = last_generated_audio_codes[:, 1:].unsqueeze(2)

        self.generated_audio_codes = torch.cat([self.generated_audio_codes, last_generated_audio_codes], dim=2)

        # apply the pattern mask to the final audio ids
        output_audio_codes = self.apply_delay_pattern_mask(self.generated_audio_codes, moshi_delay_pattern_mask)

        # revert the pattern delay mask by filtering the pad token id and bos token ids
        mask = moshi_delay_pattern_mask != self.config.audio_vocab_size

        output_audio_codes = output_audio_codes[mask].reshape(mask.shape[0], self.num_codebooks, -1)

        output_values = None
        if return_audio_waveforms:
            output_values = self.audio_encoder.decode(
                output_audio_codes,
            ).audio_values

        output_audio_codes = output_audio_codes if return_audio_codes else None

        if generation_config.return_dict_in_generate:
            return MoshiConditionalGenerationGenerateOutput(
                audio_sequences=output_values, audio_codes=output_audio_codes, **outputs
            )

        return MoshiConditionalGenerationGenerateOutput(
            audio_sequences=output_values, sequences=output_text_ids, audio_codes=output_audio_codes
        )