def forward(
        self,
        input_ids: torch.LongTensor,
        inputs_embeds: torch.Tensor,
        image_pixel_values: torch.FloatTensor | None = None,
        audio_input_features: torch.FloatTensor | None = None,
        image_sizes=None,
        image_attention_mask=None,
        audio_embed_sizes=None,
        audio_attention_mask=None,
    ) -> torch.FloatTensor:
        with torch.no_grad():
            image_position_mask = (input_ids == self.config.vision_config.image_token_id).unsqueeze(-1)
            non_image_position_mask = ~image_position_mask

        image_embeds = None
        audio_embeds = None
        if image_pixel_values is not None and (input_ids == self.image_token_id).any():
            image_embeds = self.image_embed(
                input_ids,
                inputs_embeds,
                image_pixel_values=image_pixel_values,
                image_sizes=image_sizes,
                image_attention_mask=image_attention_mask,
            )
        if audio_input_features is not None and (input_ids == self.audio_token_id).any():
            audio_projection_mode = "vision" if image_pixel_values is not None else "speech"
            audio_embeds = self.audio_embed(
                input_ids,
                inputs_embeds,
                audio_input_features=audio_input_features,
                audio_embed_sizes=audio_embed_sizes,
                audio_attention_mask=audio_attention_mask,
                audio_projection_mode=audio_projection_mode,
            )

        # merge image and audio
        if image_embeds is not None and audio_embeds is not None:
            inputs_embeds = image_embeds * image_position_mask + audio_embeds * non_image_position_mask
        elif image_embeds is not None:
            inputs_embeds = image_embeds
        elif audio_embeds is not None:
            inputs_embeds = audio_embeds

        return inputs_embeds