def forward(
        self,
        input_ids: torch.Tensor | None = None,
        attention_mask: torch.Tensor | None = None,
        inputs_embeds: torch.Tensor | None = None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> BaseModelOutput:
        if (input_ids is None) ^ (inputs_embeds is not None):
            raise ValueError("You must specify exactly one of input_ids or inputs_embeds")

        if inputs_embeds is None:
            inputs_embeds = self.embed_tokens(input_ids)

        input_shape = inputs_embeds.size()[:-1]
        embed_pos = self.embed_positions(input_shape)

        hidden_states = inputs_embeds + embed_pos
        hidden_states = nn.functional.dropout(hidden_states, p=self.dropout, training=self.training)

        if attention_mask is None:
            attention_mask = torch.ones(input_shape, device=hidden_states.device)
        attention_mask = attention_mask.long()

        # in order to use block_sparse attention, sequence_length has to be at least
        # bigger than all global attentions: 2 * block_size
        # + sliding tokens: 3 * block_size
        # + random tokens: 2 * num_random_blocks * block_size
        max_tokens_to_attend = (5 + 2 * self.config.num_random_blocks) * self.config.block_size
        if self.attention_type == "block_sparse" and input_shape[1] <= max_tokens_to_attend:
            # change attention_type from block_sparse to original_full
            sequence_length = input_shape[1]
            logger.warning(
                "Attention type 'block_sparse' is not possible if sequence_length: "
                f"{sequence_length} <= num global tokens: 2 * config.block_size "
                "+ min. num sliding tokens: 3 * config.block_size "
                "+ config.num_random_blocks * config.block_size "
                "+ additional buffer: config.num_random_blocks * config.block_size "
                f"= {max_tokens_to_attend} with config.block_size "
                f"= {self.config.block_size}, config.num_random_blocks "
                f"= {self.config.num_random_blocks}. "
                "Changing attention type to 'original_full'..."
            )
            self.set_attention_type("original_full")

        if self.attention_type == "block_sparse":
            padding_len, hidden_states, attention_mask = self._pad_to_block_size(hidden_states, attention_mask)
        else:
            padding_len = 0

        # expand attention_mask
        if self.attention_type == "original_full":
            # [bsz, seq_len] -> [bsz, 1, tgt_seq_len, src_seq_len]
            attention_mask = create_bidirectional_mask(
                config=self.config,
                inputs_embeds=inputs_embeds,
                attention_mask=attention_mask,
            )
            blocked_encoder_mask = band_mask = from_mask = to_mask = None
        elif self.attention_type == "block_sparse":
            blocked_encoder_mask, band_mask, from_mask, to_mask = self.create_masks_for_block_sparse_attn(
                attention_mask, self.block_size
            )
            attention_mask = None
        else:
            raise ValueError(
                f"attention_type can either be original_full or block_sparse, but is {self.attention_type}"
            )

        for idx, encoder_layer in enumerate(self.layers):
            # add LayerDrop (see https://huggingface.co/papers/1909.11556 for description)
            to_drop = False
            if self.training:
                dropout_probability = torch.rand([])
                if dropout_probability < self.layerdrop:  # skip the layer
                    to_drop = True

            if not to_drop:
                hidden_states = encoder_layer(
                    hidden_states,
                    attention_mask,
                    band_mask=band_mask,
                    from_mask=from_mask,
                    to_mask=to_mask,
                    from_blocked_mask=blocked_encoder_mask,
                    to_blocked_mask=blocked_encoder_mask,
                    **kwargs,
                )

        hidden_states = self.layernorm_embedding(hidden_states)

        if padding_len > 0:
            # unpad `sequence_output` because the calling function is expecting a length == input_ids.size(1)
            hidden_states = hidden_states[:, :-padding_len]

        return BaseModelOutput(
            last_hidden_state=hidden_states,
        )