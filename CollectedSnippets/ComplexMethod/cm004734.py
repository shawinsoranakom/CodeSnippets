def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        patch_lengths: torch.Tensor | None = None,
        attention_mask: torch.Tensor | None = None,
        position_ids: torch.LongTensor | None = None,
        past_key_values: Cache | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        use_cache: bool | None = None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> tuple | BaseModelOutputWithPast:
        if (input_ids is None) ^ (inputs_embeds is not None):
            raise ValueError("You must specify exactly one of input_ids or inputs_embeds")

        if use_cache:
            if past_key_values is None:
                past_key_values = EncoderDecoderCache(
                    DynamicCache(config=self.config), DynamicCache(config=self.config)
                )
            elif not isinstance(past_key_values, EncoderDecoderCache):
                # BLT uses an encoder-decoder cache even though it is not en encoder-decoder model. Create a cross-cache
                # if not yet created by the user
                past_key_values = EncoderDecoderCache(past_key_values, DynamicCache(config=self.config))

        # Extract input embeddings as early as possible
        if inputs_embeds is not None:
            encoder_embeds = inputs_embeds
            batch_size, sequence_length, _ = inputs_embeds.shape
        else:
            batch_size, sequence_length = input_ids.shape
            encoder_embeds = compute_hash_embeddings(
                input_ids,
                self.local_encoder,
                self.encoder_hash_tok_embedding,
                self.config.encoder_hash_byte_group_nb_functions,
                self.config.encoder_hash_byte_group_size,
                self.config.encoder_hash_byte_group_vocab,
            )

        if patch_lengths is None:
            if self.config.patching_mode == "entropy" and self.patcher is not None:
                if input_ids is None:
                    raise ValueError("input_ids is required for entropy-based patching")
                _, patch_lengths, _ = self.patcher(
                    input_ids,
                    patch_size=self.config.patch_size,
                    threshold=self.config.patching_threshold,
                    max_patch_length=self.config.max_patch_length,
                    patching_batch_size=self.config.patching_batch_size,
                    device=input_ids.device,
                )
            else:
                device = input_ids.device if input_ids is not None else inputs_embeds.device
                dtype = input_ids.dtype if input_ids is not None else inputs_embeds.dtype
                patch_lengths = process_patch_lengths(
                    torch.ones((batch_size, sequence_length + 1), dtype=dtype, device=device),
                    self.config.max_patch_length,
                )
        patch_ids = self._patch_ids_from_lengths(patch_lengths, sequence_length)

        if position_ids is None:
            past_seen_tokens = past_key_values.get_seq_length() if past_key_values is not None else 0
            position_ids = torch.arange(encoder_embeds.shape[1], device=encoder_embeds.device) + past_seen_tokens
            position_ids = position_ids.unsqueeze(0)

        causal_mask = create_causal_mask(
            config=self.config,
            inputs_embeds=encoder_embeds,
            attention_mask=attention_mask,
            past_key_values=past_key_values.self_attention_cache if past_key_values is not None else None,
            position_ids=position_ids,
        )

        cross_attn_mask_enc = _prepare_patch_cross_attention_mask(
            patch_ids=patch_ids,
            num_patches=patch_lengths.shape[1],
            sequence_length=sequence_length,
            patches_as_queries=True,
            cross_attn_k=self.config.cross_attn_k,
            dtype=encoder_embeds.dtype,
        )
        encoder_hidden_states, encoder_cross_states = self.local_encoder(
            input_ids=input_ids,
            inputs_embeds=encoder_embeds,
            attention_mask=causal_mask,
            position_ids=position_ids,
            encoder_attention_mask=cross_attn_mask_enc,
            num_patches=patch_lengths.shape[1],
            patch_ids=patch_ids,
            past_key_values=past_key_values.self_attention_cache if past_key_values is not None else None,
            **kwargs,
        )
        encoder_cross_states = encoder_cross_states.view(batch_size, patch_lengths.shape[1], -1)
        global_position_ids = torch.arange(0, encoder_cross_states.shape[1], device=encoder_cross_states.device)
        global_position_ids = global_position_ids.unsqueeze(0)
        global_causal_mask = create_causal_mask(
            config=self.config,
            inputs_embeds=encoder_cross_states,
            attention_mask=None,
            past_key_values=None,
            position_ids=None,
        )

        global_hidden_states = self.global_transformer(
            inputs_embeds=encoder_cross_states,
            attention_mask=global_causal_mask,
            position_ids=global_position_ids,
            **kwargs,
        )
        decoder_patch_ids = self._patch_ids_from_lengths(patch_lengths[:, 1:], sequence_length)
        cross_attn_mask_dec = _prepare_patch_cross_attention_mask(
            patch_ids=decoder_patch_ids,
            num_patches=patch_lengths.shape[1],
            sequence_length=sequence_length,
            patches_as_queries=False,
            cross_attn_k=self.config.cross_attn_k,
            dtype=encoder_embeds.dtype,
        )
        output = self.local_decoder(
            input_ids=input_ids,
            inputs_embeds=encoder_hidden_states,
            patch_embeds=global_hidden_states,
            attention_mask=causal_mask,
            position_ids=position_ids,
            past_key_values=past_key_values.cross_attention_cache if past_key_values is not None else None,
            encoder_attention_mask=cross_attn_mask_dec,
            **kwargs,
        )
        return BaseModelOutputWithPast(
            last_hidden_state=output,
            past_key_values=past_key_values,
        )