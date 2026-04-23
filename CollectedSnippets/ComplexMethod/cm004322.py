def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        position_ids: torch.LongTensor | None = None,
        attention_mask: torch.Tensor | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        use_cache: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        past_key_values: Cache | None = None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> tuple | BaseModelOutputWithNoAttention:
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        use_cache = use_cache if use_cache is not None else self.config.use_cache
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        if (input_ids is None) ^ (inputs_embeds is not None):
            raise ValueError("You must specify exactly one of input_ids or inputs_embeds")

        if self.gradient_checkpointing and self.training and use_cache:
            logger.warning_once(
                "`use_cache=True` is incompatible with gradient checkpointing. Setting `use_cache=False`."
            )
            use_cache = False

        if inputs_embeds is None:
            inputs_embeds = self.embed_tokens(input_ids)

        hidden_states = inputs_embeds

        if use_cache and past_key_values is None:
            self._setup_cache(self.config, hidden_states.shape[0], hidden_states.device, hidden_states.dtype)
            past_key_values = DynamicCache(config=self.config)

        # Hack because the mamba layer indices will stay empty in `past_key_values`, and we want `get_seq_length` and
        # `get_mask_sizes` to use the first attention layer by default for the mask function to create correct masks
        if past_key_values is not None:
            past_key_values.first_attention_layer = self.config.layers_block_type.index("attention")
            # bound new methods to this instance only
            past_key_values.get_seq_length = _get_seq_length.__get__(past_key_values)
            past_key_values.get_mask_sizes = _get_mask_sizes.__get__(past_key_values)

        if position_ids is None:
            past_seen_tokens = past_key_values.get_seq_length() if past_key_values is not None else 0
            position_ids = torch.arange(hidden_states.shape[1], device=hidden_states.device) + past_seen_tokens
            position_ids = position_ids.unsqueeze(0)

        causal_mask = create_sliding_window_causal_mask(
            config=self.config,
            inputs_embeds=inputs_embeds,
            attention_mask=attention_mask,
            past_key_values=past_key_values,
            position_ids=position_ids,
        )

        hidden_states = hidden_states * self.normalizer.type(hidden_states.dtype)

        all_hidden_states = () if output_hidden_states else None
        for i, residual_block in enumerate(self.layers):
            if output_hidden_states:
                all_hidden_states += (hidden_states,)
            hidden_states = residual_block(
                hidden_states, position_ids, causal_mask, use_cache, past_key_values, **kwargs
            )

        hidden_states = self.final_norm(hidden_states)

        # add hidden states from the last decoder layer
        if output_hidden_states:
            all_hidden_states += (hidden_states,)

        if not return_dict:
            return tuple(v for v in [hidden_states, all_hidden_states] if v is not None)

        return BaseModelOutputWithNoAttention(
            last_hidden_state=hidden_states,
            hidden_states=all_hidden_states,
        )