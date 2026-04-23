def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        pixel_values: torch.FloatTensor | None = None,
        aspect_ratio_mask: torch.Tensor | None = None,
        aspect_ratio_ids: torch.Tensor | None = None,
        attention_mask: torch.Tensor | None = None,
        cross_attention_mask: torch.Tensor | None = None,
        cross_attention_states: torch.Tensor | None = None,
        position_ids: torch.LongTensor | None = None,
        past_key_values: Cache | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        use_cache: bool | None = None,
        **kwargs: Unpack[FlashAttentionKwargs],
    ) -> BaseModelOutputWithPast:
        r"""
        aspect_ratio_mask (`torch.Tensor` of shape `(batch_size, max_num_images, max_num_tiles)`, *optional*):
            Mask to avoid performing attention on padding tiles. Mask values selected in `[0, 1]`:

            - 1 for tiles that are **not masked**,
            - 0 for tiles that are **masked**.
        aspect_ratio_ids (`torch.Tensor` of shape `(batch_size, max_num_images)`, *optional*):
            Aspect ratio ids used to select the appropriate precomputed tile embeddings based on the aspect ratio of each input image.
            These ids correspond to indices in the model's list of supported aspect ratios, offset by 1.

            For example, if the model supports aspect ratios [[1, 1], [1, 2], [2, 1]]:
            - An image with aspect ratio [1, 1] would have ID 1
            - An image with aspect ratio [1, 2] would have ID 2
            - An image with aspect ratio [2, 1] would have ID 3

            The id 0 is reserved for padding (i.e., no image).

            If an image has aspect ratio [1, 2], that means it was split into 2 tiles horizontally, and its `aspect_ratio_id` would be 2.
        cross_attention_mask (`torch.Tensor` of shape `(batch_size, seq_length, max_num_images, max_num_tiles)`, *optional*):
            Cross-attention mask to control the interaction between text tokens and image tiles.
            This 4D tensor defines which image tiles each text token should attend to.

            For each text token (in seq_length):
            - 1 indicates the token **should attend** to the corresponding image tile
            - 0 indicates the token **should not attend** to the corresponding image tile
        cross_attention_states (`torch.FloatTensor`, *optional*):
            Output of the vision model, used for cross-attention. This tensor contains the processed image features that
            the language model will attend to.
        """
        if (input_ids is None) ^ (inputs_embeds is not None):
            raise ValueError("You must specify exactly one of input_ids or inputs_embeds")

        if pixel_values is not None and cross_attention_states is not None:
            raise ValueError("`pixel_values` and `cross_attention_states` cannot be provided simultaneously")

        if pixel_values is not None:
            if aspect_ratio_ids is None:
                raise ValueError("`aspect_ratio_ids` must be provided if `pixel_values` is provided")
            # get vision tokens from vision model
            vision_outputs = self.vision_model(
                pixel_values=pixel_values,
                aspect_ratio_ids=aspect_ratio_ids,
                aspect_ratio_mask=aspect_ratio_mask,
            )
            cross_attention_states = vision_outputs.last_hidden_state
            cross_attention_states = self.multi_modal_projector(cross_attention_states).reshape(
                -1, cross_attention_states.shape[-2], self.hidden_size
            )

        if cross_attention_mask is not None:
            cross_attention_mask, full_text_row_masked_out_mask = _prepare_cross_attention_mask(
                cross_attention_mask,
                num_vision_tokens=self.vision_model.num_patches,
                dtype=self.dtype,
            )
        else:
            full_text_row_masked_out_mask = None

        if cross_attention_mask is not None:
            past_seen_tokens = past_key_values.get_seq_length() if past_key_values is not None else 0
            seq_len = input_ids.shape[1] if input_ids is not None else inputs_embeds.shape[1]
            device = input_ids.device if input_ids is not None else inputs_embeds.device
            current_pos = torch.arange(seq_len, device=device) + past_seen_tokens

            cross_attention_mask = cross_attention_mask[:, :, current_pos]
            full_text_row_masked_out_mask = full_text_row_masked_out_mask[:, :, current_pos]

        outputs = self.language_model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            position_ids=position_ids,
            cross_attention_states=cross_attention_states,
            cross_attention_mask=cross_attention_mask,
            full_text_row_masked_out_mask=full_text_row_masked_out_mask,
            past_key_values=past_key_values,
            use_cache=use_cache,
            inputs_embeds=inputs_embeds,
            **kwargs,
        )

        return BaseModelOutputWithPast(
            last_hidden_state=outputs.last_hidden_state,
            past_key_values=outputs.past_key_values,
            hidden_states=outputs.hidden_states,
            attentions=outputs.attentions,
        )