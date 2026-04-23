def forward(
        self,
        input_features: torch.FloatTensor | None = None,
        position_ids: torch.LongTensor | None = None,
        past_key_values: Cache | None = None,
        padding_cache: VoxtralRealtimeConv1dPaddingCache | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        use_cache: bool | None = None,
        use_padding_cache: bool | None = None,
        attention_mask: torch.Tensor | None = None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> tuple | BaseModelOutputWithPooling:
        r"""
        padding_cache (`VoxtralRealtimeConv1dPaddingCache`, *optional*):
            Cache for padding in convolutional layers to maintain state across streaming chunks.
        use_padding_cache (`bool`, *optional*):
            Whether to use the padding cache.
        """
        if (input_features is None) ^ (inputs_embeds is not None):
            raise ValueError("You must specify exactly one of input_features or inputs_embeds")

        if use_padding_cache and padding_cache is None:
            padding_cache = VoxtralRealtimeConv1dPaddingCache()

        if inputs_embeds is None:
            inputs_embeds = self.embedder(input_features, padding_cache)

        if use_cache and past_key_values is None:
            past_key_values = DynamicCache(config=self.config)

        if position_ids is None:
            past_seen_tokens = past_key_values.get_seq_length() if past_key_values is not None else 0
            position_ids = torch.arange(inputs_embeds.shape[1], device=inputs_embeds.device) + past_seen_tokens
            position_ids = position_ids.unsqueeze(0)

        mask_function = create_causal_mask if self.config.sliding_window is None else create_sliding_window_causal_mask
        causal_mask = mask_function(
            config=self.config,
            inputs_embeds=inputs_embeds,
            attention_mask=attention_mask,
            past_key_values=past_key_values,
            position_ids=position_ids,
        )
        hidden_states = inputs_embeds
        position_embeddings = self.rotary_emb(hidden_states, position_ids=position_ids)

        for encoder_layer in self.layers:
            hidden_states = encoder_layer(
                hidden_states,
                attention_mask=causal_mask,
                position_embeddings=position_embeddings,
                position_ids=position_ids,
                past_key_values=past_key_values,
                use_cache=use_cache,
                **kwargs,
            )

        hidden_states = self.norm(hidden_states)
        return VoxtralRealtimeEncoderOutput(
            last_hidden_state=hidden_states,
            past_key_values=past_key_values,
            padding_cache=padding_cache,
        )