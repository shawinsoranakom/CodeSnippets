def forward(
        self,
        input_ids: torch.Tensor | None = None,
        attention_mask: torch.Tensor | None = None,
        token_type_ids: torch.Tensor | None = None,
        position_ids: torch.Tensor | None = None,
        inputs_embeds: torch.Tensor | None = None,
        encoder_hidden_states: torch.Tensor | None = None,
        encoder_attention_mask: torch.Tensor | None = None,
        past_key_values: list[torch.FloatTensor] | None = None,
        use_cache: bool | None = None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> tuple[torch.Tensor] | BaseModelOutputWithPoolingAndCrossAttentions:
        r"""
        token_type_ids (`torch.LongTensor` of shape `(batch_size, sequence_length)`, *optional*):
            Segment token indices to indicate first and second portions of the inputs. Indices are selected in `[0,1]`:

            - 0 corresponds to a *sentence A* token,
            - 1 corresponds to a *sentence B* token.
            This parameter can only be used when the model is initialized with `type_vocab_size` parameter with value
            >= 2. All the value in this tensor should be always < type_vocab_size.

            [What are token type IDs?](../glossary#token-type-ids)
        """
        if (input_ids is None) ^ (inputs_embeds is not None):
            raise ValueError("You must specify exactly one of input_ids or inputs_embeds")

        if self.config.is_decoder:
            use_cache = use_cache if use_cache is not None else self.config.use_cache
        else:
            use_cache = False

        if use_cache and past_key_values is None:
            past_key_values = (
                EncoderDecoderCache(DynamicCache(config=self.config), DynamicCache(config=self.config))
                if encoder_hidden_states is not None or self.config.is_encoder_decoder
                else DynamicCache(config=self.config)
            )

        past_key_values_length = past_key_values.get_seq_length() if past_key_values is not None else 0

        embedding_output = self.embeddings(
            input_ids=input_ids,
            position_ids=position_ids,
            token_type_ids=token_type_ids,
            inputs_embeds=inputs_embeds,
            past_key_values_length=past_key_values_length,
        )

        attention_mask, encoder_attention_mask = self._create_attention_masks(
            attention_mask=attention_mask,
            encoder_attention_mask=encoder_attention_mask,
            embedding_output=embedding_output,
            encoder_hidden_states=encoder_hidden_states,
            past_key_values=past_key_values,
        )

        encoder_outputs = self.encoder(
            embedding_output,
            attention_mask=attention_mask,
            encoder_hidden_states=encoder_hidden_states,
            encoder_attention_mask=encoder_attention_mask,
            past_key_values=past_key_values,
            use_cache=use_cache,
            position_ids=position_ids,
            **kwargs,
        )
        sequence_output = encoder_outputs[0]
        sequence_output = self.LayerNorm(sequence_output)
        pooled_output = self.pooler(sequence_output) if self.pooler is not None else None

        return BaseModelOutputWithPoolingAndCrossAttentions(
            last_hidden_state=sequence_output,
            pooler_output=pooled_output,
            past_key_values=encoder_outputs.past_key_values,
        )