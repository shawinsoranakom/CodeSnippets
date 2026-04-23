def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        attention_mask: torch.Tensor | None = None,
        position_ids: torch.LongTensor | None = None,
        past_key_values: Cache | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        pixel_values: torch.Tensor | None = None,
        image_grid_thw: torch.LongTensor | None = None,
        images_per_sample: torch.LongTensor | None = None,
        rope_deltas: torch.LongTensor | None = None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> tuple | GlmImageModelOutputWithPast:
        r"""
        image_grid_thw (`torch.LongTensor` of shape `(total_images_in_batch, 3)`, *optional*):
            The temporal, height and width of feature shape of each image in LLM.
            Images are packed across all samples in the batch.
        images_per_sample (`torch.LongTensor` of shape `(batch_size,)`, *optional*):
            Number of images (including target grids) for each sample in the batch.
        rope_deltas (`torch.LongTensor` of shape `(batch_size, )`, *optional*):
            The rope index difference between sequence length and multimodal rope.
        """
        if (input_ids is None) ^ (inputs_embeds is not None):
            raise ValueError("You must specify exactly one of input_ids or inputs_embeds")

        batch_size = input_ids.shape[0] if input_ids is not None else inputs_embeds.shape[0]

        if pixel_values is not None:
            # Process source images (image-to-image mode)
            # Source images are identified by counting image_end_token_id in input_ids
            # Note: We must exclude padding tokens since pad_token_id == image_end_token_id
            if images_per_sample is not None:
                grids_per_sample = torch.split(image_grid_thw, images_per_sample.tolist())
                # Create mask for non-padding tokens (attention_mask=1 means non-padding)
                # Handle 4D attention mask (from static cache) by extracting diagonal
                if attention_mask is not None and attention_mask.ndim == 4:
                    non_pad_mask = torch.diagonal(attention_mask[:, 0], dim1=1, dim2=2)
                    if non_pad_mask.dtype.is_floating_point:
                        non_pad_mask = non_pad_mask / torch.finfo(non_pad_mask.dtype).min
                        non_pad_mask = (1.0 - non_pad_mask).int()
                    # Only keep columns matching input_ids length
                    non_pad_mask = non_pad_mask[:, -input_ids.shape[1] :]
                else:
                    non_pad_mask = attention_mask if attention_mask is not None else torch.ones_like(input_ids)

                source_grids_list = []
                is_image_end = input_ids == self.config.image_end_token_id
                is_non_pad = non_pad_mask == 1
                num_source_per_sample = (is_image_end & is_non_pad).sum(dim=1).tolist()
                for sample_idx in range(batch_size):
                    num_source = num_source_per_sample[sample_idx]
                    if num_source > 0:
                        source_grids_list.append(grids_per_sample[sample_idx][:num_source])
                if len(source_grids_list) == 0:
                    raise ValueError(
                        "pixel_values provided but no source images found in input_ids. "
                        "Ensure input_ids contains image_end_token_id for each source image."
                    )
                source_grids = torch.cat(source_grids_list, dim=0)
            else:
                # Fallback for batch_size=1: all but last grid are source images
                source_grids = image_grid_thw[:-1]

            image_features = self.get_image_features(pixel_values, source_grids, return_dict=True)
            image_embeds = torch.cat(image_features.pooler_output, dim=0)
            image_ids = self.get_image_tokens(image_embeds, source_grids)
            image_ids = image_ids.view(-1).to(input_ids.device)
            special_image_mask = self.get_placeholder_mask(input_ids, image_ids)
            input_ids = input_ids.masked_scatter(special_image_mask, image_ids)

        if inputs_embeds is None:
            inputs_embeds = self.get_input_embeddings()(input_ids)

        if position_ids is None:
            position_ids = self.compute_3d_position_ids(
                input_ids=input_ids,
                image_grid_thw=image_grid_thw,
                images_per_sample=images_per_sample,
                inputs_embeds=inputs_embeds,
                attention_mask=attention_mask,
                past_key_values=past_key_values,
            )

        outputs = self.language_model(
            input_ids=None,
            position_ids=position_ids,
            attention_mask=attention_mask,
            past_key_values=past_key_values,
            inputs_embeds=inputs_embeds,
            **kwargs,
        )

        return GlmImageModelOutputWithPast(
            last_hidden_state=outputs.last_hidden_state,
            past_key_values=outputs.past_key_values,
            hidden_states=outputs.hidden_states,
            attentions=outputs.attentions,
            rope_deltas=self.rope_deltas,
        )