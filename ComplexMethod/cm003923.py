def forward(
        self,
        input_ids: torch.Tensor | None = None,
        attention_mask: torch.Tensor | None = None,
        image_embeds: torch.Tensor | None = None,
        image_embeds_position_mask: torch.Tensor | None = None,
        past_key_values: Cache | None = None,
        inputs_embeds: torch.Tensor | None = None,
        position_ids: torch.Tensor | None = None,
        use_cache: bool | None = None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> BaseModelOutputWithPastAndCrossAttentions:
        if (input_ids is None) ^ (inputs_embeds is not None):
            raise ValueError(
                "You cannot specify both input_ids and inputs_embeds at the same time, and must specify either one"
            )

        # The argument `inputs_embeds` should be the one without being multiplied by `self.embed_scale`.
        if inputs_embeds is None:
            inputs_embeds = self.embed_tokens(input_ids)

        # Ignore copy
        if image_embeds is not None:
            inputs_embeds = inputs_embeds.clone()
            inputs_embeds[image_embeds_position_mask == 1] = image_embeds.to(inputs_embeds.device).view(
                -1, image_embeds.shape[-1]
            )

        inputs_embeds = inputs_embeds * self.embed_scale

        # embed positions
        positions = self.embed_positions(
            input_ids=input_ids,
            inputs_embeds=inputs_embeds,
            past_key_values_length=0,
            position_ids=position_ids,
        )
        positions = positions.to(inputs_embeds.device)

        # Ignore copy
        if image_embeds_position_mask is not None:
            # make every not equal 0 be 1
            image_embeds_position_mask = image_embeds_position_mask.ne(0).long()
            segment_embeds = self.segment_emb(image_embeds_position_mask).to(positions.device)
            positions += segment_embeds
        else:
            # add zero embedding for padding tokens
            bsz, seq_len, dim = positions.size()
            zero_emb = self.segment_emb(
                torch.zeros((bsz, 1), dtype=torch.long, device=self.segment_emb.weight.device)
            ).to(positions.device)
            positions += zero_emb

        hidden_states = inputs_embeds + positions

        hidden_states = nn.functional.dropout(hidden_states, p=self.dropout, training=self.training)

        if use_cache and past_key_values is None:
            past_key_values = DynamicCache(config=self.config)

        causal_mask = create_causal_mask(
            config=self.config,
            inputs_embeds=inputs_embeds,
            attention_mask=attention_mask,
            past_key_values=past_key_values,
        )

        hidden_states = nn.functional.dropout(hidden_states, p=self.dropout, training=self.training)

        for decoder_layer in self.layers:
            hidden_states = decoder_layer(
                hidden_states,
                attention_mask=causal_mask,
                past_key_values=past_key_values,
                use_cache=use_cache,
                **kwargs,
            )

        # add final layer norm
        hidden_states = self.layer_norm(hidden_states)

        return BaseModelOutputWithPast(
            last_hidden_state=hidden_states,
            past_key_values=past_key_values if use_cache else None,
        )