def forward(
        self,
        hidden_states: torch.Tensor,
        attention_mask: torch.FloatTensor | None = None,
        encoder_hidden_states: torch.FloatTensor | None = None,
        encoder_attention_mask: torch.FloatTensor | None = None,
        past_key_values: Cache | None = None,
        use_cache: bool | None = None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> BaseModelOutputWithPastAndCrossAttentions:
        if self.gradient_checkpointing and self.training:
            if use_cache:
                logger.warning(
                    "`use_cache=True` is incompatible with gradient checkpointing. Setting `use_cache=False`..."
                )
                use_cache = False

        if use_cache:
            # The model acts as encoder decoder but is not an encoder decoder. So we cast all cache objects to
            # `EncoderDecoderCache` type assuming that the incoming cache is from `self_attention`
            if isinstance(past_key_values, DynamicCache):
                past_key_values = EncoderDecoderCache(past_key_values, DynamicCache(config=self.config))
            elif past_key_values is None:
                past_key_values = EncoderDecoderCache(
                    DynamicCache(config=self.config), DynamicCache(config=self.config)
                )

        for layer_module in self.layer:
            hidden_states = layer_module(
                hidden_states,
                encoder_hidden_states,
                attention_mask=attention_mask,
                encoder_attention_mask=encoder_attention_mask,
                past_key_values=past_key_values,
                **kwargs,
            )

        return BaseModelOutputWithPastAndCrossAttentions(
            last_hidden_state=hidden_states,
            past_key_values=past_key_values,
        )