def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        attention_mask: torch.Tensor | None = None,
        position_ids: torch.LongTensor | None = None,
        past_key_values: EncoderDecoderCache | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        use_cache: bool | None = None,
        encoder_hidden_states: torch.Tensor | None = None,
        encoder_attention_mask: torch.Tensor | None = None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> BaseModelOutputWithPastAndCrossAttentions:
        if (input_ids is None) ^ (inputs_embeds is not None):
            raise ValueError("You must specify exactly one of input_ids or inputs_embeds")
        if encoder_hidden_states is None:
            raise ValueError("`encoder_hidden_states` must be given in decoder")

        if inputs_embeds is None:
            inputs_embeds = self.embed_tokens(input_ids)

        if not self.training and use_cache and past_key_values is None:
            past_key_values = EncoderDecoderCache(DynamicCache(config=self.config), DynamicCache())

        if position_ids is None:
            past_seen_tokens = past_key_values.get_seq_length() if past_key_values is not None else 0
            position_ids = torch.arange(inputs_embeds.shape[1], device=inputs_embeds.device) + past_seen_tokens
            position_ids = position_ids.unsqueeze(0)

        if not isinstance(self_attn_mask_mapping := attention_mask, dict):
            # this masking function does nothing to masking but forces `allow_is_causal_skip` to be False
            # as we always need a mask during decoding for merged attention.
            dummy_and_mask_function = lambda *args: torch.tensor(True, dtype=torch.bool)  # noqa
            mask_kwargs = {
                "config": self.config,
                "inputs_embeds": inputs_embeds,
                "attention_mask": attention_mask,
                "past_key_values": past_key_values.self_attention_cache if past_key_values is not None else None,
                "position_ids": position_ids,
                "and_mask_function": dummy_and_mask_function,
            }
            self_attn_mask_mapping = {
                "full_attention": create_causal_mask(**mask_kwargs),
                "sliding_attention": create_sliding_window_causal_mask(**mask_kwargs),
            }

        if not isinstance(cross_attn_mask_mapping := encoder_attention_mask, dict):
            cross_attn_mask_mapping = {
                "full_attention": create_bidirectional_mask(
                    config=self.config,
                    inputs_embeds=inputs_embeds,
                    attention_mask=encoder_attention_mask,
                    encoder_hidden_states=encoder_hidden_states,
                    and_mask_function=dummy_and_mask_function,
                )
            }

        merged_attn_mask_mapping = {
            "full_attention": torch.cat(
                [self_attn_mask_mapping["full_attention"], cross_attn_mask_mapping["full_attention"]], dim=-1
            ),
            "sliding_attention": torch.cat(
                [self_attn_mask_mapping["sliding_attention"], cross_attn_mask_mapping["full_attention"]], dim=-1
            ),
        }

        # input layer
        hidden_states = inputs_embeds

        # global and local position embeddings
        position_embeddings = {}
        for layer_type in set(self.config.layer_types):
            position_embeddings[layer_type] = self.rotary_emb(hidden_states, position_ids, layer_type)

        # dropout
        hidden_states = self.dropout(hidden_states)

        for i, layer_module in enumerate(self.layers[: self.config.num_hidden_layers]):
            hidden_states = layer_module(
                hidden_states,
                position_embeddings[self.config.layer_types[i]],
                merged_attn_mask_mapping[self.config.layer_types[i]],
                position_ids,
                past_key_values,
                use_cache,
                encoder_hidden_states,
                **kwargs,
            )

        hidden_states = self.norm(hidden_states)
        hidden_states = self.dropout(hidden_states)
        return BaseModelOutputWithPastAndCrossAttentions(
            last_hidden_state=hidden_states,
            past_key_values=past_key_values,
        )