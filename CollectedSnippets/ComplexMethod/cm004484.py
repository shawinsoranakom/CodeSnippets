def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        pixel_values: torch.FloatTensor | None = None,
        pixel_values_videos: torch.FloatTensor | None = None,
        attention_mask: torch.Tensor | None = None,
        position_ids: torch.LongTensor | None = None,
        past_key_values: Cache | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        use_cache: bool | None = None,
        logits_to_keep: int | torch.Tensor = 0,
        **lm_kwargs,
    ) -> tuple | PerceptionLMModelOutputWithPast:
        if (input_ids is None) ^ (inputs_embeds is not None):
            raise ValueError("You must specify exactly one of input_ids or inputs_embeds")
        if (pixel_values is not None or pixel_values_videos is not None) and inputs_embeds is not None:
            raise ValueError(
                "You cannot specify both (pixel_values or pixel_values_videos) and inputs_embeds at the same time, and must specify either one"
            )

        if inputs_embeds is None:
            inputs_embeds = self.get_input_embeddings()(input_ids)

        image_features = None
        if pixel_values is not None:
            image_features = self.get_image_features(pixel_values=pixel_values, return_dict=True).pooler_output
            image_features = image_features.to(inputs_embeds.device, dtype=inputs_embeds.dtype)
            special_image_mask, _ = self.get_placeholder_mask(
                input_ids, inputs_embeds=inputs_embeds, image_features=image_features
            )
            inputs_embeds = inputs_embeds.masked_scatter(special_image_mask, image_features)

        video_features = None
        if pixel_values_videos is not None:
            video_features = self.get_image_features(pixel_values=pixel_values_videos, return_dict=True).pooler_output
            video_features = video_features.to(inputs_embeds.device, dtype=inputs_embeds.dtype)
            _, special_video_mask = self.get_placeholder_mask(
                input_ids, inputs_embeds=inputs_embeds, video_features=video_features
            )
            inputs_embeds = inputs_embeds.masked_scatter(special_video_mask, video_features)

        outputs = self.language_model(
            attention_mask=attention_mask,
            position_ids=position_ids,
            past_key_values=past_key_values,
            inputs_embeds=inputs_embeds,
            use_cache=use_cache,
            return_dict=True,
            logits_to_keep=logits_to_keep,
            **lm_kwargs,
        )
        return PerceptionLMModelOutputWithPast(
            last_hidden_state=outputs.last_hidden_state,
            hidden_states=outputs.hidden_states,
            past_key_values=outputs.past_key_values,
            attentions=outputs.attentions,
            image_hidden_states=image_features if pixel_values is not None else None,
            video_hidden_states=(video_features if pixel_values_videos is not None else None),
        )