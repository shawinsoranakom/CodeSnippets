def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        past_key_values: Cache | None = None,
        attention_mask: torch.FloatTensor | None = None,
        token_type_ids: torch.LongTensor | None = None,
        position_ids: torch.LongTensor | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        encoder_hidden_states: torch.Tensor | None = None,
        encoder_attention_mask: torch.FloatTensor | None = None,
        use_cache: bool | None = None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> BaseModelOutputWithPastAndCrossAttentions:
        if (input_ids is None) ^ (inputs_embeds is not None):
            raise ValueError("You must specify exactly one of input_ids or inputs_embeds")

        if inputs_embeds is None:
            inputs_embeds = self.wte(input_ids)

        if token_type_ids is not None:
            token_type_ids = token_type_ids.view(-1, inputs_embeds.shape[1])

        # based on pattern from src/transformers/models/whisper/modeling_whisper.py::WhisperDecoder and similar addition in GPT2Model
        if use_cache:
            if past_key_values is None:
                past_key_values = DynamicCache(config=self.config)

            if self.config.add_cross_attention and not isinstance(past_key_values, EncoderDecoderCache):
                past_key_values = EncoderDecoderCache(past_key_values, DynamicCache(config=self.config))

        if position_ids is None:
            past_seen_tokens = past_key_values.get_seq_length() if past_key_values is not None else 0
            position_ids = torch.arange(inputs_embeds.shape[1], device=inputs_embeds.device) + past_seen_tokens
            position_ids = position_ids.unsqueeze(0)

        # Attention mask.
        attention_mask = create_causal_mask(
            config=self.config,
            inputs_embeds=inputs_embeds,
            attention_mask=attention_mask,
            past_key_values=past_key_values,
            position_ids=position_ids,
        )

        encoder_attention_mask = None
        if encoder_hidden_states is not None:
            encoder_attention_mask = create_bidirectional_mask(
                config=self.config,
                inputs_embeds=inputs_embeds,
                attention_mask=encoder_attention_mask,
                encoder_hidden_states=encoder_hidden_states,
            )

        position_embeds = self.wpe(position_ids)
        hidden_states = inputs_embeds + position_embeds

        if token_type_ids is not None:
            token_type_embeds = self.wte(token_type_ids)
            hidden_states = hidden_states + token_type_embeds

        hidden_states = self.drop(hidden_states)

        output_shape = (
            -1,
            inputs_embeds.shape[1],
        ) + (hidden_states.size(-1),)

        for block in self.h:
            hidden_states = block(
                hidden_states,
                past_key_values if not (self.gradient_checkpointing and self.training) else None,
                attention_mask,
                encoder_hidden_states,  # as a positional argument for gradient checkpointing
                encoder_attention_mask=encoder_attention_mask,
                use_cache=use_cache,
                **kwargs,
            )

        hidden_states = self.ln_f(hidden_states)

        hidden_states = hidden_states.view(output_shape)

        past_key_values = past_key_values if use_cache else None
        return BaseModelOutputWithPastAndCrossAttentions(
            last_hidden_state=hidden_states,
            past_key_values=past_key_values,
        )