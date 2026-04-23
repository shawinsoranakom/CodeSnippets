def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        attention_mask: torch.Tensor | None = None,
        position_ids: torch.LongTensor | None = None,
        past_key_values: Cache | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        pixel_values: torch.FloatTensor | None = None,
        image_encoder_embeddings: torch.FloatTensor | None = None,
        perceiver_embeddings: torch.FloatTensor | None = None,
        image_attention_mask: torch.Tensor | None = None,
        use_cache: bool | None = None,
        interpolate_pos_encoding: bool | None = False,
        **kwargs: Unpack[TransformersKwargs],
    ) -> tuple | IdeficsBaseModelOutputWithPast:
        r"""
        image_encoder_embeddings (`torch.FloatTensor`, *optional*):
            The output of the image encoder.
        perceiver_embeddings (`torch.FloatTensor`, *optional*):
            The output of the perceiver resampler.
        image_attention_mask (`torch.LongTensor`, *optional*):
            The attention mask for the image encoder.
        """
        device = input_ids.device if input_ids is not None else inputs_embeds.device

        if (input_ids is None) ^ (inputs_embeds is not None):
            raise ValueError("You must specify exactly one of input_ids or inputs_embeds")

        if inputs_embeds is None:
            inputs_embeds = self.embed_tokens(input_ids)

        if use_cache and past_key_values is None:
            past_key_values = DynamicCache(config=self.config)

        seq_length = inputs_embeds.shape[1]
        past_key_values_length = past_key_values.get_seq_length() if past_key_values is not None else 0
        seq_length_with_past = seq_length + past_key_values_length

        if attention_mask is not None and position_ids is None:
            # create position_ids on the fly for batch generation
            position_ids = attention_mask.long().cumsum(-1) - 1
            position_ids.masked_fill_(attention_mask == 0, 1)
            position_ids = position_ids[:, -seq_length:]
        elif position_ids is None:
            position_ids = torch.arange(seq_length, device=inputs_embeds.device) + past_key_values_length
            position_ids = position_ids.unsqueeze(0)

        if sum(x is None for x in [pixel_values, image_encoder_embeddings, perceiver_embeddings]) != 2:
            raise ValueError(
                "Exactly 1 of pixel_values, image_encoder_embeddings or perceiver_embeddings has to be not-None."
            )

        elif pixel_values is not None:
            pixel_values = pixel_values.to(dtype=self.dtype, device=device)  # fp16 compatibility
            batch_size, num_images = pixel_values.shape[:2]
            pixel_values = pixel_values.contiguous().view(batch_size * num_images, *pixel_values.shape[2:])

            # Get sequence from the vision encoder
            image_hidden_states = self.vision_model(
                pixel_values=pixel_values, interpolate_pos_encoding=interpolate_pos_encoding
            ).last_hidden_state

        elif image_encoder_embeddings is not None:
            batch_size, num_images, image_seq_len, image_hidden_size = image_encoder_embeddings.size()
            image_hidden_states = image_encoder_embeddings.to(dtype=self.dtype, device=device)
            image_hidden_states = image_hidden_states.view(batch_size * num_images, image_seq_len, image_hidden_size)

        if self.config.use_resampler:
            if perceiver_embeddings is None:
                perceiver_embeddings = self.perceiver_resampler(image_hidden_states)
                image_seq_len, image_hidden_size = perceiver_embeddings.size(1), perceiver_embeddings.size(2)
            else:
                batch_size, num_images, image_seq_len, image_hidden_size = perceiver_embeddings.size()
            image_hidden_states = perceiver_embeddings
        elif perceiver_embeddings is None:
            image_seq_len, image_hidden_size = image_hidden_states.size(1), image_hidden_states.size(2)
        else:
            raise ValueError("If `perceiver_embeddings` are passed, use_resampler should be True")

        image_hidden_states = image_hidden_states.view(batch_size, num_images * image_seq_len, image_hidden_size)
        # # Hack to use the model in full language modeling mode
        # image_attention_mask = torch.zeros(batch_size, seq_length, 1, dtype=torch.long, device=image_hidden_states.device)
        # Make image_attention_mask compatible with hidden states
        text_seq_len = image_attention_mask.size(1)
        image_attention_mask = image_attention_mask.unsqueeze(-1)
        image_attention_mask = image_attention_mask.repeat(1, 1, 1, image_seq_len)
        image_attention_mask = image_attention_mask.view(batch_size, text_seq_len, num_images * image_seq_len)

        if image_hidden_states is not None:
            image_batch_size, image_sequence_length, _ = image_hidden_states.size()
            image_hidden_shape = (image_batch_size, image_sequence_length)
            if image_attention_mask is None:
                image_attention_mask = torch.ones(image_hidden_shape, device=device)
            image_attention_mask = self.invert_attention_mask(image_attention_mask)
        else:
            image_attention_mask = None

        # cross_attention_gate:
        # For any tokens attending to no images, the hidden_states coming out of the cross-attention should be zeroed-out.
        # `image_attention_mask` has shape [bsz, 1, num_images, hidden_size] with elements equal to either 0.0 or a very negative number.
        # If any of the elements are 0.0, then the token is attending to at least one image and the gate value is 1. Otherwise the gate value is 0.
        # `cross_attention_gate` has shape [bsz, seq_len] with elements equal to either 0.0 or 1.0.
        cross_attention_gate = ((((image_attention_mask == 0.0).any(dim=-1)).to(dtype=self.dtype)).squeeze(dim=1)).to(
            device
        )

        # embed positions
        if attention_mask is None:
            attention_mask = torch.ones(
                (batch_size, seq_length_with_past), dtype=torch.bool, device=inputs_embeds.device
            )

        causal_mask = create_causal_mask(
            config=self.config,
            inputs_embeds=inputs_embeds,
            attention_mask=attention_mask,
            past_key_values=past_key_values,
            position_ids=position_ids,
        )

        hidden_states = inputs_embeds

        for idx, decoder_layer in enumerate(self.layers):
            # TODO(ls): Add cross attention values to respective lists
            if idx % self.cross_layer_interval == 0:
                cross_attn_block = self.gated_cross_attn_layers[idx // self.cross_layer_interval]
                hidden_states = cross_attn_block(
                    hidden_states,
                    causal_mask,
                    image_hidden_states,
                    image_attention_mask=image_attention_mask,
                    cross_attention_gate=cross_attention_gate,
                    past_key_values=None,  # not implemented
                    **kwargs,
                )

            hidden_states = decoder_layer(
                hidden_states,
                attention_mask=causal_mask,
                position_ids=position_ids,
                past_key_values=past_key_values,
                **kwargs,
            )

        hidden_states = self.norm(hidden_states)
        image_hidden_states = image_hidden_states.view(batch_size, num_images, image_seq_len, image_hidden_size)

        return IdeficsBaseModelOutputWithPast(
            last_hidden_state=hidden_states,
            image_hidden_states=image_hidden_states,
            past_key_values=past_key_values,
        )