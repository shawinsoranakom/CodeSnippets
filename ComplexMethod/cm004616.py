def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        attention_mask: torch.Tensor | None = None,
        position_ids: torch.LongTensor | None = None,
        past_key_values: Cache | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        image_pixel_values: torch.FloatTensor | None = None,
        image_sizes: torch.LongTensor | None = None,
        image_attention_mask=None,
        audio_input_features: torch.FloatTensor | None = None,
        audio_embed_sizes=None,
        audio_attention_mask=None,
        use_cache: bool | None = None,
        **kwargs,
    ) -> tuple | BaseModelOutputWithPast:
        r"""
        image_pixel_values (`torch.FloatTensor`, *optional*):
            If the input contains images, these correspond to the pixel values after transformations (as returned by
            the Processor)
        image_sizes (`torch.LongTensor`, *optional*):
            If the input contains images, these correspond to size of each image.
        image_attention_mask (`torch.LongTensor`, *optional*):
            Attention mask for the images.
        audio_input_features (`torch.FloatTensor`, *optional*):
            If the input contains audio samples, these correspond to the values after transformation (as returned by
            the Processor).
        audio_embed_sizes (`torch.Tensor`, *optional*):
            Size of the audio inputs.
        audio_attention_mask (`torch.Tensor, *optional*):
            Attention mask for the audio inputs.
        """
        if (input_ids is None) ^ (inputs_embeds is not None):
            raise ValueError("You must specify exactly one of input_ids or inputs_embeds")
        if use_cache and past_key_values is None:
            past_key_values = DynamicCache(config=self.config)

        if inputs_embeds is None:
            inputs_embeds = self.embed_tokens(input_ids)
            inputs_embeds = self.embed_tokens_extend(
                input_ids,
                inputs_embeds,
                image_pixel_values=image_pixel_values,
                audio_input_features=audio_input_features,
                image_sizes=image_sizes,
                image_attention_mask=image_attention_mask,
                audio_embed_sizes=audio_embed_sizes,
                audio_attention_mask=audio_attention_mask,
            )

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

        for decoder_layer in self.layers:
            hidden_states = decoder_layer(
                hidden_states,
                attention_mask=causal_mask,
                position_ids=position_ids,
                past_key_values=past_key_values,
                use_cache=use_cache,
                position_embeddings=position_embeddings,
                **kwargs,
            )

        hidden_states = self.norm(hidden_states)
        return BaseModelOutputWithPast(
            last_hidden_state=hidden_states,
            past_key_values=past_key_values if use_cache else None,
        )