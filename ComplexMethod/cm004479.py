def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        pixel_values: torch.FloatTensor | None = None,
        attention_mask: torch.Tensor | None = None,
        position_ids: torch.LongTensor | None = None,
        past_key_values: Cache | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        labels: torch.LongTensor | None = None,
        use_cache: bool | None = None,
        logits_to_keep: int | torch.Tensor = 0,
        **kwargs,
    ) -> tuple | Ovis2ModelOutputWithPast:
        if (input_ids is None) ^ (inputs_embeds is not None):
            raise ValueError("You must specify exactly one of input_ids or inputs_embeds")

        if inputs_embeds is None:
            inputs_embeds = self.get_input_embeddings()(input_ids)

        if pixel_values is not None:
            image_outputs = self.get_image_features(pixel_values=pixel_values, return_dict=True)
            image_features = image_outputs.pooler_output
            visual_indicator_features = image_outputs.visual_indicator_features

            special_image_mask = self.get_placeholder_mask(
                input_ids,
                inputs_embeds=inputs_embeds,
                image_features=image_features,
            )
            inputs_embeds = inputs_embeds.masked_scatter(special_image_mask, image_features)

            for i, visual_indicator_id in enumerate(self.visual_indicator_token_ids):
                if input_ids is None:
                    mask = inputs_embeds == self.get_input_embeddings()(
                        torch.tensor(visual_indicator_id, dtype=torch.long, device=inputs_embeds.device)
                    )
                    mask = mask.all(-1)
                else:
                    mask = (input_ids == visual_indicator_id).to(inputs_embeds.device)

                if mask.any():
                    inputs_embeds[mask] = (
                        visual_indicator_features[i]
                        .expand_as(inputs_embeds[mask])
                        .to(inputs_embeds.device, inputs_embeds.dtype)
                    )

        outputs = self.language_model(
            attention_mask=attention_mask,
            position_ids=position_ids,
            past_key_values=past_key_values,
            inputs_embeds=inputs_embeds,
            use_cache=use_cache,
            logits_to_keep=logits_to_keep,
            **kwargs,
        )

        return Ovis2ModelOutputWithPast(
            last_hidden_state=outputs.last_hidden_state,
            past_key_values=outputs.past_key_values,
            hidden_states=outputs.hidden_states,
            attentions=outputs.attentions,
            image_hidden_states=image_features if pixel_values is not None else None,
        )