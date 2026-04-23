def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        attention_mask: torch.Tensor | None = None,
        encoder_hidden_states: torch.FloatTensor | None = None,
        encoder_attention_mask: torch.LongTensor | None = None,
        past_key_values: Cache | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        use_cache: bool | None = None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> BaseModelOutputWithPastAndCrossAttentions:
        if (input_ids is None) ^ (inputs_embeds is not None):
            raise ValueError("You cannot specify both decoder_input_ids and decoder_inputs_embeds at the same time")

        if inputs_embeds is None:
            inputs_embeds = self.embed_tokens(input_ids)

        # Important to apply outside of the above `if`, in case user passes `embeds`
        inputs_embeds = inputs_embeds * self.embed_scale

        # initialize `past_key_values`
        if use_cache and past_key_values is None:
            past_key_values = (
                EncoderDecoderCache(DynamicCache(config=self.config), DynamicCache(config=self.config))
                if encoder_hidden_states is not None or self.config.is_encoder_decoder
                else DynamicCache(config=self.config)
            )

        batch_size, seq_length = inputs_embeds.size()[:-1]
        past_key_values_length = past_key_values.get_seq_length() if past_key_values is not None else 0
        position_ids = torch.arange(seq_length, device=inputs_embeds.device) + past_key_values_length

        if attention_mask is None and not is_torchdynamo_compiling():
            # required mask seq length can be calculated via length of past cache
            mask_seq_length = past_key_values_length + seq_length
            attention_mask = torch.ones(batch_size, mask_seq_length, device=inputs_embeds.device)

        self_attn_cache = (
            past_key_values.self_attention_cache
            if isinstance(past_key_values, EncoderDecoderCache)
            else past_key_values
        )

        causal_mask = create_causal_mask(
            config=self.config,
            inputs_embeds=inputs_embeds,
            attention_mask=attention_mask,
            past_key_values=self_attn_cache,
        )
        encoder_attention_mask = create_bidirectional_mask(
            config=self.config,
            inputs_embeds=inputs_embeds,
            attention_mask=encoder_attention_mask,
            encoder_hidden_states=encoder_hidden_states,
        )

        # embed positions
        position_ids = self.embed_positions(
            (batch_size, seq_length), past_key_values_length, position_ids=position_ids
        )
        hidden_states = inputs_embeds + position_ids
        hidden_states = nn.functional.dropout(hidden_states, p=self.dropout, training=self.training)

        for idx, decoder_layer in enumerate(self.layers):
            # add LayerDrop (see https://huggingface.co/papers/1909.11556 for description)
            if self.training:
                dropout_probability = torch.rand([])
                if dropout_probability < self.layerdrop:
                    continue

            hidden_states = decoder_layer(
                hidden_states,
                causal_mask,
                encoder_hidden_states,  # as a positional argument for gradient checkpointing
                encoder_attention_mask=encoder_attention_mask,
                past_key_values=past_key_values,
                use_cache=use_cache,
                **kwargs,
            )
        return BaseModelOutputWithPastAndCrossAttentions(
            last_hidden_state=hidden_states,
            past_key_values=past_key_values,
        )