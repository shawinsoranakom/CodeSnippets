def forward(
        self,
        action_embeds: torch.Tensor,  # aka `suffix_emb` (noise + state + timestep)
        input_ids: torch.Tensor | None = None,
        pixel_values: torch.Tensor | None = None,
        attention_mask: torch.Tensor | None = None,
        pixel_attention_mask: torch.Tensor | None = None,
        position_ids: torch.LongTensor | None = None,
        inputs_embeds: torch.Tensor | None = None,  # aka `prefix_emb` or merged image+text emb
        past_key_values: Cache | None = None,  # must-have for prefix tuning
        **kwargs,
    ) -> BaseModelOutputWithPast:
        r"""
        action_embeds (`torch.Tensor`, *optional*):
            The embeddings of input actions and robot states.
        pixel_attention_mask (`torch.Tensor`, *optional*):
            The mask indicating padded positions in the input image.
        """
        if pixel_values is not None and past_key_values is None:
            if attention_mask is not None and position_ids is None:
                position_ids = attention_mask.cumsum(-1) - 1

            if inputs_embeds is None:
                inputs_embeds = self.embed_prefix(input_ids, pixel_values, pixel_attention_mask)

            token_type_ids = torch.zeros_like(inputs_embeds)[:, :, 0]
            past_key_values = self.vlm(
                inputs_embeds=inputs_embeds,
                attention_mask=attention_mask,
                position_ids=position_ids,
                token_type_ids=token_type_ids,
                use_cache=True,
            ).past_key_values

        if attention_mask is not None and attention_mask.ndim != 2:
            raise ValueError("Only two-dimensional attention masks are accepted for now!")

        # Merge masks if needed, same for position ids
        dit_position_ids = dit_attention_mask = None
        if attention_mask is not None:
            noise_mask = torch.ones(
                action_embeds.shape[0],
                action_embeds.shape[1],
                dtype=attention_mask.dtype,
                device=attention_mask.device,
            )
            dit_attention_mask = torch.cat([attention_mask, noise_mask], dim=1)
            dit_position_ids = (torch.cumsum(dit_attention_mask, dim=1) - 1)[:, -action_embeds.shape[1] :]

        # We have three blocks: vlm-inputss, state and actions from which only 1 token is `state`
        # The mask should be bidirectional within each block and to prev blocks, but not to next blocks
        vlm_input_length = past_key_values.get_seq_length()
        block_sizes = torch.tensor([vlm_input_length + 1, action_embeds.shape[1] - 1], device=action_embeds.device)
        block_boundaries = torch.cumsum(block_sizes, dim=0) - 1
        bidirectional_mask = create_bidirectional_mask(
            config=self.config.dit_config,
            inputs_embeds=action_embeds,
            attention_mask=dit_attention_mask,
            past_key_values=past_key_values,
            and_mask_function=blockwise_bidirectional_mask(block_boundaries),
        )

        dit_output = self.dit(
            inputs_embeds=action_embeds,
            attention_mask=bidirectional_mask,
            position_ids=dit_position_ids,
            past_key_values=past_key_values,
            **kwargs,
        )
        return dit_output