def _prepare_inputs_embeds_for_generation(
        self,
        input_ids: torch.LongTensor | None = None,
        user_input_values: torch.FloatTensor | None = None,
        user_audio_codes: torch.Tensor | None = None,
        moshi_input_values: torch.FloatTensor | None = None,
        moshi_audio_codes: torch.Tensor | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        attention_mask: torch.Tensor | None = None,
        generation_config: GenerationConfig | None = None,
        apply_delay_pattern_mask: bool = False,
        concat_unconditional_inputs: bool = False,
    ):
        user_delay_pattern_mask = None
        moshi_delay_pattern_mask = None

        if (
            inputs_embeds is None
            and input_ids is None
            and user_input_values is None
            and user_audio_codes is None
            and moshi_input_values is None
            and moshi_audio_codes is None
        ):
            raise ValueError(
                "You must provide at least one of `input_ids`, `user_input_values`, `moshi_input_values`, `user_audio_codes`, `moshi_audio_codes` or `inputs_embeds`."
            )

        # in case inputs_embeds is passed, we might still need to create delay pattern masks
        if inputs_embeds is None or apply_delay_pattern_mask:
            if user_input_values is not None and user_audio_codes is None:
                user_audio_codes = self.audio_encoder.encode(user_input_values, num_quantizers=self.num_codebooks)[0]

            if moshi_input_values is not None and moshi_audio_codes is None:
                moshi_audio_codes = self.audio_encoder.encode(moshi_input_values, num_quantizers=self.num_codebooks)[0]

        if inputs_embeds is None and concat_unconditional_inputs:
            unconditional_inputs = self.get_unconditional_inputs(num_samples=user_audio_codes.shape[0])
            moshi_audio_codes = torch.cat([unconditional_inputs.moshi_audio_codes, moshi_audio_codes], dim=2)
            user_audio_codes = torch.cat([unconditional_inputs.user_audio_codes, user_audio_codes], dim=2)
            input_ids = torch.cat([unconditional_inputs.input_ids, input_ids], dim=1)
            if attention_mask is not None:
                attention_mask = torch.cat([unconditional_inputs.attention_mask, attention_mask], dim=1)

        if inputs_embeds is None or apply_delay_pattern_mask:
            if apply_delay_pattern_mask and user_audio_codes is not None:
                user_audio_codes, user_delay_pattern_mask = self.build_delay_pattern_mask(
                    user_audio_codes,
                    bos_token_id=self.config.audio_vocab_size,
                    pad_token_id=self.config.audio_vocab_size,
                    max_length=generation_config.max_length,
                )

            if apply_delay_pattern_mask and moshi_audio_codes is not None:
                moshi_audio_codes, moshi_delay_pattern_mask = self.build_delay_pattern_mask(
                    moshi_audio_codes,
                    bos_token_id=self.config.audio_vocab_size,
                    pad_token_id=self.config.audio_vocab_size,
                    max_length=generation_config.max_length,
                )

        # If inputs_embeds is provided, it has the priority over input_ids and audio_codes, which won't be used
        if inputs_embeds is None:
            audio_inputs_embeds = None
            if user_audio_codes is not None and moshi_audio_codes is not None:
                audio_codes = torch.cat([moshi_audio_codes, user_audio_codes], dim=1)
                audio_inputs_embeds = sum(
                    self.embed_tokens[codebook](audio_codes[:, codebook]) for codebook in range(audio_codes.shape[1])
                )
            elif moshi_audio_codes is not None:
                audio_codes = moshi_audio_codes
                audio_inputs_embeds = sum(
                    self.embed_tokens[codebook](audio_codes[:, codebook]) for codebook in range(audio_codes.shape[1])
                )
            elif user_audio_codes is not None:
                audio_codes = user_audio_codes
                audio_inputs_embeds = sum(
                    self.embed_tokens[codebook](audio_codes[:, codebook + self.num_codebooks])
                    for codebook in range(audio_codes.shape[1])
                )

            if input_ids is not None:
                inputs_embeds = self.decoder.model.embed_tokens(input_ids)

            if audio_inputs_embeds is not None:
                inputs_embeds = (
                    audio_inputs_embeds
                    if inputs_embeds is None
                    else audio_inputs_embeds + inputs_embeds.to(audio_inputs_embeds.device)
                )

        return (
            inputs_embeds,
            input_ids,
            user_audio_codes,
            moshi_audio_codes,
            user_delay_pattern_mask,
            moshi_delay_pattern_mask,
            attention_mask,
        )