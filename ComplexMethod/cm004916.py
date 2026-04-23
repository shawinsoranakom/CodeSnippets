def forward(
        self,
        input_ids=None,
        attention_mask=None,
        inputs_embeds=None,
        output_hidden_states=None,
        **kwargs: Unpack[TransformersKwargs],
    ):
        r"""
        Args:
            input_ids (`torch.LongTensor` of shape `(batch_size, sequence_length)`):
                Indices of input sequence tokens in the vocabulary. Padding will be ignored by default should you
                provide it.

                Indices can be obtained using [`AutoTokenizer`]. See [`PreTrainedTokenizer.encode`] and
                [`PreTrainedTokenizer.__call__`] for details.

                [What are input IDs?](../glossary#input-ids)
            attention_mask (`torch.Tensor` of shape `(batch_size, sequence_length)`, *optional*):
                Mask to avoid performing attention on padding token indices. Mask values selected in `[0, 1]`:

                - 1 for tokens that are **not masked**,
                - 0 for tokens that are **masked**.

                [What are attention masks?](../glossary#attention-mask)

            inputs_embeds (`torch.FloatTensor` of shape `(batch_size, sequence_length, hidden_size)`, *optional*):
                Optionally, instead of passing `input_ids` you can choose to directly pass an embedded representation.
                This is useful if you want more control over how to convert `input_ids` indices into associated vectors
                than the model's internal embedding lookup matrix.
            output_attentions (`bool`, *optional*):
                Whether or not to return the attentions tensors of all attention layers. See `attentions` under
                returned tensors for more detail.
            output_hidden_states (`bool`, *optional*):
                Whether or not to return the hidden states of all layers. See `hidden_states` under returned tensors
                for more detail.
        """
        # We need to treat this special because it only adds the last global state which is unique
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )

        if (input_ids is None) ^ (inputs_embeds is not None):
            raise ValueError("You must specify exactly one of input_ids or inputs_embeds")

        if inputs_embeds is None:
            inputs_embeds = self.embed_tokens(input_ids)

        embed_pos = self.embed_positions(inputs_embeds)

        hidden_states = inputs_embeds + embed_pos
        hidden_states = nn.functional.dropout(hidden_states, p=self.dropout, training=self.training)

        batch_size, seq_len, _ = hidden_states.shape

        # Setup mask
        if attention_mask is None:
            attention_mask = torch.ones(
                *inputs_embeds.shape[:-1], dtype=inputs_embeds.dtype, device=inputs_embeds.device
            )
        attention_mask = attention_mask.to(dtype=hidden_states.dtype)
        mask_min_value = torch.finfo(hidden_states.dtype).min
        inverted_mask = 1.0 - attention_mask
        attention_mask = inverted_mask.masked_fill(
            inverted_mask.to(torch.bool),
            mask_min_value,
        )

        # padding to block_size
        if seq_len % self.config.block_size != 0:
            pad_len = self.config.block_size - seq_len % self.config.block_size
            hidden_states = nn.functional.pad(hidden_states, pad=(0, 0, 0, pad_len), value=0)
            attention_mask = nn.functional.pad(attention_mask, pad=(0, pad_len), value=mask_min_value)

        # Global tokens
        global_hidden_states = self.embed_global(
            torch.arange(self.config.num_global_tokens, device=hidden_states.device)[None].expand(batch_size, -1)
        )

        encoder_states = () if output_hidden_states else None
        for encoder_layer in self.layers:
            if output_hidden_states:
                encoder_states = encoder_states + (hidden_states,)
            # add LayerDrop (see https://huggingface.co/papers/1909.11556 for description)
            to_drop = False
            if self.training:
                dropout_probability = torch.rand([])
                if dropout_probability < self.layerdrop:  # skip the layer
                    to_drop = True

            if to_drop:
                hidden_states, global_hidden_states = (None, None)
            else:
                hidden_states, global_hidden_states = encoder_layer(
                    hidden_states,
                    global_hidden_states,
                    attention_mask,
                    **kwargs,
                )

        # Undo padding-to-block-size
        hidden_states = hidden_states[:, :seq_len]

        hidden_states = self.layer_norm(hidden_states)

        if output_hidden_states:
            encoder_states = encoder_states + ((hidden_states, global_hidden_states),)

        return BaseModelOutput(last_hidden_state=hidden_states, hidden_states=encoder_states)