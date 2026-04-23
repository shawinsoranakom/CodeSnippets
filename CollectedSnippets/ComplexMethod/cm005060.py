def forward(
        self,
        input_ids: torch.Tensor | None = None,
        attention_mask: torch.Tensor | None = None,
        encoder_hidden_states: torch.Tensor | None = None,
        encoder_attention_mask: torch.Tensor | None = None,
        past_key_values: Cache | None = None,
        inputs_embeds: torch.Tensor | None = None,
        use_cache: bool | None = None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> tuple | BaseModelOutputWithPastAndCrossAttentions:
        if inputs_embeds is None:
            inputs_embeds = self.embed_tokens(input_ids)

        # initialize `past_key_values`
        if use_cache and past_key_values is None:
            past_key_values = EncoderDecoderCache(DynamicCache(config=self.config), DynamicCache(config=self.config))

        past_key_values_length = past_key_values.get_seq_length() if past_key_values is not None else 0

        attention_mask = create_causal_mask(
            config=self.config,
            inputs_embeds=inputs_embeds,
            attention_mask=attention_mask,
            past_key_values=past_key_values,
        )
        encoder_attention_mask = create_bidirectional_mask(
            config=self.config,
            inputs_embeds=inputs_embeds,
            attention_mask=encoder_attention_mask,
            encoder_hidden_states=encoder_hidden_states,
        )

        # embed positions
        positions = self.embed_positions(input_ids, inputs_embeds, past_key_values_length)
        positions = positions.to(inputs_embeds.device)

        hidden_states = inputs_embeds + positions
        hidden_states = nn.functional.dropout(hidden_states, p=self.dropout, training=self.training)

        synced_gpus = is_deepspeed_zero3_enabled() or is_fsdp_managed_module(self)

        for idx, decoder_layer in enumerate(self.layers):
            # add LayerDrop (see https://huggingface.co/papers/1909.11556 for description)
            dropout_probability = torch.rand([])
            skip_the_layer = self.training and dropout_probability < self.layerdrop
            if not skip_the_layer or synced_gpus:
                hidden_states = decoder_layer(
                    hidden_states,
                    attention_mask,
                    encoder_hidden_states,  # as a positional argument for gradient checkpointing
                    encoder_attention_mask=encoder_attention_mask,
                    past_key_values=past_key_values,
                    use_cache=use_cache,
                    **kwargs,
                )

            if skip_the_layer:
                continue

        last_hidden_states = self.layer_norm(hidden_states)

        return MoEModelOutputWithPastAndCrossAttentions(
            last_hidden_state=last_hidden_states, past_key_values=past_key_values
        )