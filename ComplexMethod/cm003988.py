def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        pixel_values: torch.FloatTensor | None = None,
        pixel_values_videos: torch.FloatTensor | None = None,
        input_features: torch.FloatTensor | None = None,
        attention_mask: torch.Tensor | None = None,
        input_features_mask: torch.Tensor | None = None,
        position_ids: torch.LongTensor | None = None,
        past_key_values: Cache | None = None,
        mm_token_type_ids: torch.LongTensor | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        use_cache: bool | None = None,
        image_position_ids: torch.LongTensor | None = None,
        video_position_ids: torch.LongTensor | None = None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> Gemma4ModelOutputWithPast:
        r"""
        input_features_mask (`torch.FloatTensor]` of shape `(num_images, seq_length)`):
            The attention mask for the input audio.
        image_position_ids (`torch.LongTensor` of shape `(batch_size, max_patches, 2)`, *optional*):
            2D patch position coordinates from the image processor, with `(-1, -1)` indicating padding.
            Passed through to the vision encoder for positional embedding computation.
        video_position_ids (`torch.LongTensor` of shape `(num_videos, num_frames, max_patches, 2)`, *optional*):
            2D patch position coordinates from the video processor, with `(-1, -1)` indicating padding.
            Passed through to the vision encoder for positional embedding computation.
        """
        if (input_ids is None) ^ (inputs_embeds is not None):
            raise ValueError("You must specify exactly one of input_ids or inputs_embeds")

        image_mask, video_mask, audio_mask = self.get_placeholder_mask(input_ids, inputs_embeds)
        multimodal_mask = image_mask | video_mask | audio_mask

        # Replace image id with PAD if the image token if OOV, to avoid index-errors
        llm_input_ids = None
        if inputs_embeds is None:
            llm_input_ids = input_ids.clone()
            llm_input_ids[multimodal_mask] = self.config.text_config.pad_token_id
            inputs_embeds = self.get_input_embeddings()(llm_input_ids)

        if self.config.get_text_config().hidden_size_per_layer_input:
            pad_embedding = self.language_model.embed_tokens.weight[self.config.text_config.pad_token_id, :]
            llm_inputs_embeds = torch.where(multimodal_mask[..., None], pad_embedding.view(1, 1, -1), inputs_embeds)
            per_layer_inputs = self.language_model.get_per_layer_inputs(llm_input_ids, llm_inputs_embeds)
        else:
            per_layer_inputs = None

        # Merge text and images
        if pixel_values is not None:
            image_features = self.get_image_features(pixel_values, image_position_ids, return_dict=True).pooler_output
            image_features = image_features.to(inputs_embeds.device, inputs_embeds.dtype)

            # Confirm the number of soft tokens from the vision tower matches the number of slots in the embeddings.
            n_image_tokens = image_mask.sum()
            image_mask = image_mask.unsqueeze(-1).expand_as(inputs_embeds).to(inputs_embeds.device)
            torch_compilable_check(
                inputs_embeds[image_mask].numel() == image_features.numel(),
                f"Image features and image tokens do not match, tokens: {n_image_tokens}, features:"
                f" {image_features.shape[0]}",
            )

            inputs_embeds = inputs_embeds.masked_scatter(
                image_mask.to(inputs_embeds.device), image_features.to(inputs_embeds.device)
            )

        if pixel_values_videos is not None:
            video_features = self.get_video_features(
                pixel_values_videos, video_position_ids, return_dict=True
            ).pooler_output
            video_features = video_features.to(inputs_embeds.device, inputs_embeds.dtype)

            # Confirm the number of soft tokens from the vision tower matches the number of slots in the embeddings.
            n_video_tokens = video_mask.sum()
            video_mask = video_mask.unsqueeze(-1).expand_as(inputs_embeds).to(inputs_embeds.device)
            torch_compilable_check(
                inputs_embeds[video_mask].numel() == video_features.numel(),
                f"Video features and video tokens do not match, tokens: {n_video_tokens}, features:"
                f" {video_features.shape[0]}",
            )

            inputs_embeds = inputs_embeds.masked_scatter(
                video_mask.to(inputs_embeds.device), video_features.to(inputs_embeds.device)
            )

        # Merge text and audio
        if input_features is not None and input_features_mask is not None:
            audio_output = self.get_audio_features(input_features, input_features_mask, return_dict=True)
            audio_features = audio_output.pooler_output
            audio_mask_from_encoder = audio_output.attention_mask  # True = valid

            # Strip padding tokens: only keep real (non-padding) audio soft tokens.
            # audio_mask_from_encoder is True for valid positions, False for padding tokens.
            # This mirrors the vision encoder's padding stripping (see Gemma4VisionEncoder.forward).
            audio_features = audio_features[audio_mask_from_encoder]

            n_audio_tokens = audio_mask.sum()
            audio_mask = audio_mask.unsqueeze(-1).expand_as(inputs_embeds).to(inputs_embeds.device)
            torch_compilable_check(
                inputs_embeds[audio_mask].numel() == audio_features.numel(),
                f"Audio features and audio tokens do not match, tokens: {n_audio_tokens}, features:"
                f" {audio_features.shape[0] * audio_features.shape[1]}",
            )

            inputs_embeds = inputs_embeds.masked_scatter(
                audio_mask.to(inputs_embeds.device), audio_features.to(inputs_embeds.device)
            )

        # It may already have been prepared by, e.g., `generate`
        if position_ids is None:
            past_seen_tokens = past_key_values.get_seq_length() if past_key_values is not None else 0
            position_ids = torch.arange(inputs_embeds.shape[1], device=inputs_embeds.device) + past_seen_tokens
            position_ids = position_ids.unsqueeze(0)

        if not isinstance(causal_mask_mapping := attention_mask, dict):
            if self.config.get_text_config().use_bidirectional_attention == "vision":
                # Larger Gemma 4 models use Gemma 3's bidirectional attention mask for vision inputs
                causal_mask_mapping = create_causal_mask_mapping(
                    self.config,
                    inputs_embeds=inputs_embeds,
                    attention_mask=attention_mask,
                    past_key_values=past_key_values,
                    position_ids=position_ids,
                    mm_token_type_ids=mm_token_type_ids,
                )
            else:
                # Smaller Gemma models use a conventional casual attention mask
                causal_mask_mapping = create_masks_for_generate(
                    self.config,
                    inputs_embeds,
                    attention_mask,
                    past_key_values,
                    position_ids,
                )

        outputs = self.language_model(
            per_layer_inputs=per_layer_inputs,
            attention_mask=causal_mask_mapping,
            position_ids=position_ids,
            past_key_values=past_key_values,
            inputs_embeds=inputs_embeds,
            use_cache=use_cache,
            return_dict=True,
            **kwargs,
        )

        return Gemma4ModelOutputWithPast(
            last_hidden_state=outputs.last_hidden_state,
            past_key_values=outputs.past_key_values,
            hidden_states=outputs.hidden_states,
            attentions=outputs.attentions,
            image_hidden_states=image_features if pixel_values is not None else None,
            audio_hidden_states=audio_features if input_features is not None else None,
        )