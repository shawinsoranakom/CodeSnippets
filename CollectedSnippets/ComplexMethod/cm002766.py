def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        attention_mask: torch.FloatTensor | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        past_key_values: Cache | None = None,
        use_cache: bool | None = None,
        position_ids: torch.LongTensor | None = None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> tuple | BaseModelOutputWithPastAndCrossAttentions:
        if (input_ids is None) ^ (inputs_embeds is not None):
            raise ValueError("You cannot specify both decoder_input_ids and decoder_inputs_embeds at the same time")

        if inputs_embeds is None:
            inputs_embeds = self.embed_tokens(input_ids)

        # initialize past_key_values
        if use_cache and past_key_values is None:
            past_key_values = DynamicCache(config=self.config)

        batch_size, seq_length = inputs_embeds.size()[:-1]
        past_key_values_length = past_key_values.get_seq_length() if past_key_values is not None else 0

        if attention_mask is None:
            # required mask seq length can be calculated via length of past cache
            mask_seq_length = past_key_values_length + seq_length
            attention_mask = torch.ones(batch_size, mask_seq_length, device=inputs_embeds.device)

        self_attn_cache = past_key_values

        causal_mask = create_causal_mask(
            config=self.config,
            input_embeds=inputs_embeds,
            attention_mask=attention_mask,
            past_key_values=self_attn_cache,
        )

        # embed positions
        if position_ids is None:
            position_ids = torch.arange(seq_length, device=inputs_embeds.device) + past_key_values_length
            position_ids = position_ids.unsqueeze(0)

        positions = self.embed_positions(attention_mask, past_key_values_length, position_ids=position_ids)
        hidden_states = inputs_embeds + positions
        hidden_states = nn.functional.dropout(hidden_states, p=self.dropout, training=self.training)

        for idx, decoder_layer in enumerate(self.layers):
            if self.training:
                dropout_probability = torch.rand([])
                if dropout_probability < self.layerdrop:
                    continue

            hidden_states = decoder_layer(
                hidden_states,
                attention_mask=causal_mask,
                past_key_values=past_key_values,
                use_cache=use_cache,
                position_ids=position_ids,
                **kwargs,
            )

        hidden_states = self.layer_norm(hidden_states)

        return BaseModelOutputWithPastAndCrossAttentions(
            last_hidden_state=hidden_states,
            past_key_values=past_key_values,
        )