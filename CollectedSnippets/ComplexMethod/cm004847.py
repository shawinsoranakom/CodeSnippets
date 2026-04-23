def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        pixel_values: torch.FloatTensor | None = None,
        high_res_pixel_values: torch.FloatTensor | None = None,
        attention_mask: torch.Tensor | None = None,
        position_ids: torch.LongTensor | None = None,
        past_key_values: Cache | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        use_cache: bool | None = None,
        logits_to_keep: int | torch.Tensor = 0,
        **kwargs,
    ) -> DeepseekVLHybridBaseModelOutputWithPast:
        if (input_ids is None) ^ (inputs_embeds is not None):
            raise ValueError(
                "You cannot specify both input_ids and inputs_embeds at the same time, and must specify either one"
            )

        if pixel_values is not None and high_res_pixel_values is None:
            raise ValueError("Both pixel_values and high_res_pixel_values should be specified at the same time")

        if inputs_embeds is None:
            inputs_embeds = self.get_input_embeddings()(input_ids)

        if pixel_values is not None:
            if input_ids is None:
                image_attention_mask = inputs_embeds == self.get_input_embeddings()(
                    torch.tensor(self.config.image_token_id, dtype=torch.long, device=inputs_embeds.device)
                )
                image_attention_mask = image_attention_mask.all(-1)
            else:
                image_attention_mask = input_ids == self.config.image_token_id

            image_attention_mask = image_attention_mask.unsqueeze(-1).expand_as(inputs_embeds).to(inputs_embeds.device)
            image_embeds = self.get_image_features(pixel_values, high_res_pixel_values, return_dict=True).pooler_output
            image_features = image_embeds.reshape(-1, inputs_embeds.shape[-1])
            image_features = image_features.to(inputs_embeds.device, inputs_embeds.dtype)
            inputs_embeds = inputs_embeds.masked_scatter(image_attention_mask, image_features)

        lm_output = self.language_model(
            inputs_embeds=inputs_embeds,
            attention_mask=attention_mask,
            position_ids=position_ids,
            past_key_values=past_key_values,
            use_cache=use_cache,
            logits_to_keep=logits_to_keep,
            **kwargs,
        )

        return DeepseekVLHybridBaseModelOutputWithPast(
            last_hidden_state=lm_output.last_hidden_state,
            past_key_values=lm_output.past_key_values,
            hidden_states=lm_output.hidden_states,
            attentions=lm_output.attentions,
            image_hidden_states=image_embeds if pixel_values is not None else None,
        )