def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        attention_mask: torch.Tensor | None = None,
        position_ids: torch.LongTensor | None = None,
        cross_attention_states: torch.FloatTensor | None = None,
        cross_attention_mask: torch.Tensor | None = None,
        full_text_row_masked_out_mask: tuple[torch.Tensor, torch.Tensor] | None = None,
        past_key_values: Cache | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        use_cache: bool | None = None,
        **kwargs: Unpack[FlashAttentionKwargs],
    ) -> BaseModelOutputWithPast:
        r"""
        cross_attention_states (`torch.FloatTensor`, *optional*):
            Output of the vision model, used for cross-attention. This tensor contains the processed image features that
            the language model will attend to.
        cross_attention_mask (`torch.Tensor` of shape `(batch_size, seq_length, max_num_images, max_num_tiles)`, *optional*):
            Cross-attention mask to control the interaction between text tokens and image tiles.
            This 4D tensor defines which image tiles each text token should attend to.

            For each text token (in seq_length):
            - 1 indicates the token **should attend** to the corresponding image tile
            - 0 indicates the token **should not attend** to the corresponding image tile
        full_text_row_masked_out_mask (`tuple[torch.Tensor, torch.Tensor]`, *optional*):
            A tuple containing two tensors that mask out rows in the cross-attention mechanism:
            - The first tensor has shape `(batch_size, 1, seq_length, 1)` and contains values of 0 or 1.
              A value of 0 indicates that the corresponding text token's entire row in the cross-attention
              matrix should be masked out (all image tokens ignored).
            - The second tensor has the same shape and is used internally to apply the masking during
              the forward pass of cross-attention layers.
            This mask is derived from the cross_attention_mask and is used to handle cases where a text token
            should not attend to any image token.

        Example:

        ```python
        >>> from transformers import AutoProcessor, MllamaTextModel

        >>> checkpoint = "meta-llama/Llama-3.2-11B-Vision"
        >>> model = MllamaTextModel.from_pretrained(checkpoint)
        >>> processor = AutoProcessor.from_pretrained(checkpoint)

        >>> text = "<|image|>If I had to write a haiku for this one"
        >>> inputs = processor(text=text, return_tensors="pt")

        >>> output = model(**inputs)

        >>> print(output.last_hidden_state.shape)
        torch.Size([1, 13, 4096])
        ```
        """
        use_cache = use_cache if use_cache is not None else self.config.use_cache

        if (input_ids is None) ^ (inputs_embeds is not None):
            raise ValueError("You must specify exactly one of input_ids or inputs_embeds")

        if inputs_embeds is None:
            inputs_embeds = self.embed_tokens(input_ids)

        hidden_states = inputs_embeds

        if use_cache and past_key_values is None:
            past_key_values = DynamicCache(config=self.config)

        if position_ids is None:
            past_seen_tokens = past_key_values.get_seq_length() if past_key_values is not None else 0
            position_ids = torch.arange(inputs_embeds.shape[1], device=inputs_embeds.device) + past_seen_tokens
            position_ids = position_ids.unsqueeze(0)

        causal_mask = create_causal_mask(
            config=self.config,
            inputs_embeds=inputs_embeds,
            attention_mask=attention_mask,
            past_key_values=past_key_values,
            position_ids=position_ids,
        )
        position_embeddings = self.rotary_emb(hidden_states, position_ids=position_ids)

        # decoder layers
        for idx, decoder_layer in enumerate(self.layers):
            # For text-only path we should skip cross attention layers.
            # Let's check if the layer is cross attention layer and if we have cross attention states
            # or cached cross attention states.
            is_cross_attention_layer = idx in self.cross_attention_layers
            is_cross_attention_cache_empty = past_key_values is None or (
                past_key_values is not None and past_key_values.get_seq_length(idx) == 0
            )

            if is_cross_attention_layer and cross_attention_states is None and is_cross_attention_cache_empty:
                continue

            hidden_states = decoder_layer(
                hidden_states,
                cross_attention_states=cross_attention_states,
                cross_attention_mask=cross_attention_mask,
                attention_mask=causal_mask,
                full_text_row_masked_out_mask=full_text_row_masked_out_mask,
                position_ids=position_ids,
                past_key_values=past_key_values,
                use_cache=use_cache,
                position_embeddings=position_embeddings,
                **kwargs,
            )

        hidden_states = self.norm(hidden_states)

        return BaseModelOutputWithPast(
            last_hidden_state=hidden_states,
            past_key_values=past_key_values,
        )