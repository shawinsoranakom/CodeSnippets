def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        attention_mask: torch.Tensor | None = None,
        position_ids: torch.LongTensor | None = None,
        past_key_values: Cache | None = None,
        labels: torch.LongTensor | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        use_cache: bool | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        pixel_values: torch.Tensor | None = None,
        image_grid_thw: torch.LongTensor | None = None,
        **kwargs,
    ) -> ColQwen2ForRetrievalOutput:
        r"""
        image_grid_thw (`torch.LongTensor` of shape `(num_images, 3)`, *optional*):
            The temporal, height and width of feature shape of each image in LLM.
        """
        # Handle the custom "pixel_values" input obtained with `ColQwen2Processor` through unpadding
        if pixel_values is not None and image_grid_thw is not None:
            # NOTE: image_grid_thw: (batch_size, 3) where image_grid_thw[i] = (num_patches_h, num_patches_w, temporal_patch_size)
            offsets = image_grid_thw[:, 1] * image_grid_thw[:, 2]  # (batch_size,)
            arange = torch.arange(pixel_values.shape[1], device=offsets.device)  # (max_len,)
            mask = arange.unsqueeze(0) < offsets.unsqueeze(1)  # (batch_size, max_len)
            pixel_values = pixel_values[mask]  # (total_valid_patches, channels, height, width)

        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions

        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        # Custom data preparation to fix an issue with the gradient flow when training with multiple GPUs.
        if inputs_embeds is None:
            inputs_embeds = self.vlm.get_input_embeddings()(input_ids)

            if pixel_values is not None:
                image_embeds = self.vlm.visual(pixel_values, grid_thw=image_grid_thw, return_dict=True).pooler_output
                image_mask = (
                    (input_ids == self.config.vlm_config.image_token_id).unsqueeze(-1).expand_as(inputs_embeds)
                )
                image_embeds = image_embeds.to(inputs_embeds.device, inputs_embeds.dtype)
                inputs_embeds = inputs_embeds.masked_scatter(image_mask, image_embeds)

        vlm_output = self.vlm(
            input_ids=None,
            position_ids=position_ids,
            attention_mask=attention_mask,
            past_key_values=past_key_values,
            inputs_embeds=inputs_embeds,
            use_cache=use_cache,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )

        vlm_hidden_states = vlm_output.hidden_states if output_hidden_states else None

        last_hidden_states = vlm_output[0]  # (batch_size, sequence_length, hidden_size)
        proj_dtype = self.embedding_proj_layer.weight.dtype
        embeddings = self.embedding_proj_layer(last_hidden_states.to(proj_dtype))  # (batch_size, sequence_length, dim)

        # L2 normalization
        embeddings = embeddings / embeddings.norm(dim=-1, keepdim=True)  # (batch_size, sequence_length, dim)
        if attention_mask is not None:
            embeddings = embeddings * attention_mask.unsqueeze(-1)  # (batch_size, sequence_length, dim)

        return ColQwen2ForRetrievalOutput(
            embeddings=embeddings,
            past_key_values=vlm_output.past_key_values,
            hidden_states=vlm_hidden_states,
            attentions=vlm_output.attentions,
        )