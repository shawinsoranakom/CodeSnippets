def forward(
        self,
        input_ids=None,
        attention_mask=None,
        global_attention_mask=None,
        inputs_embeds=None,
        output_attentions=None,
        output_hidden_states=None,
        return_dict=None,
        **kwargs,
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
            global_attention_mask (`torch.FloatTensor` of shape `(batch_size, sequence_length)`, *optional*):
                Mask to decide the attention given on each token, local attention or global attention for the encoder.
                Tokens with global attention attends to all other tokens, and all other tokens attend to them. This is
                important for task-specific finetuning because it makes the model more flexible at representing the
                task. For example, for classification, the <s> token should be given global attention. For QA, all
                question tokens should also have global attention. Please refer to the [Longformer
                paper](https://huggingface.co/papers/2004.05150) for more details. Mask values selected in `[0, 1]`:

                - 0 for local attention (a sliding window attention),
                - 1 for global attention (tokens that attend to all other tokens, and all other tokens attend to them).
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
            return_dict (`bool`, *optional*):
                Whether or not to return a [`~utils.ModelOutput`] instead of a plain tuple.
        """
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        # check input_ids and inputs_embeds
        if input_ids is not None and inputs_embeds is not None:
            raise ValueError("You cannot specify both input_ids and inputs_embeds at the same time")
        elif input_ids is None and inputs_embeds is None:
            raise ValueError("You have to specify either input_ids or inputs_embeds")

        if inputs_embeds is None:
            inputs_embeds = self.embed_tokens(input_ids)

        # create default attention_mask
        if attention_mask is None:
            attention_mask = torch.ones(inputs_embeds.size()[:-1], device=inputs_embeds.device, dtype=torch.long)

        # merge `global_attention_mask` and `attention_mask`
        if global_attention_mask is not None:
            attention_mask = self._merge_to_attention_mask(attention_mask, global_attention_mask)

        # pad input if necessary
        padding_len, input_ids, attention_mask, inputs_embeds = self._pad_to_window_size(
            input_ids=input_ids,
            attention_mask=attention_mask,
            inputs_embeds=inputs_embeds,
            pad_token_id=self.config.pad_token_id,
        )

        # retrieve input_shape
        if input_ids is not None:
            input_shape = input_ids.size()
            input_ids = input_ids.view(-1, input_shape[-1])
        elif inputs_embeds is not None:
            input_shape = inputs_embeds.size()[:-1]

        # convert attention_mask to float
        if attention_mask is not None:
            # [bsz, seq_len] -> [bsz, seq_len]; 1 -> 0.0; 0 -> "-inf"
            attention_mask = _prepare_4d_attention_mask_inverted(attention_mask, inputs_embeds.dtype)[:, 0, 0, :]

        # get masking tensors
        is_index_masked = attention_mask < 0
        is_index_global_attn = attention_mask > 0
        is_global_attn = is_index_global_attn.flatten().any().item()

        embed_pos = self.embed_positions(input_shape)

        hidden_states = inputs_embeds + embed_pos
        hidden_states = self.layernorm_embedding(hidden_states)
        hidden_states = nn.functional.dropout(hidden_states, p=self.dropout, training=self.training)

        encoder_states = () if output_hidden_states else None
        all_attentions = () if output_attentions else None
        all_global_attentions = () if (output_attentions and is_global_attn) else None

        for idx, encoder_layer in enumerate(self.layers):
            if output_hidden_states:
                encoder_states = encoder_states + (hidden_states,)
            # add LayerDrop (see https://huggingface.co/papers/1909.11556 for description)
            dropout_probability = torch.rand([])

            if self.training and (dropout_probability < self.layerdrop):  # skip the layer
                layer_outputs = (None, None, None)
            else:
                layer_outputs = encoder_layer(
                    hidden_states,
                    attention_mask=attention_mask,
                    is_index_masked=is_index_masked,
                    is_index_global_attn=is_index_global_attn,
                    is_global_attn=is_global_attn,
                    output_attentions=output_attentions,
                )
                hidden_states = layer_outputs[0]

            if output_attentions:
                # bzs x seq_len x num_attn_heads x (num_global_attn + attention_window_len + 1) => bzs x num_attn_heads x seq_len x (num_global_attn + attention_window_len + 1)
                all_attentions = all_attentions + (layer_outputs[1].transpose(1, 2),)

                if is_global_attn:
                    # bzs x num_attn_heads x num_global_attn x seq_len => bzs x num_attn_heads x seq_len x num_global_attn
                    all_global_attentions = all_global_attentions + (layer_outputs[2].transpose(2, 3),)

        if output_hidden_states:
            encoder_states = encoder_states + (hidden_states,)

        # undo padding
        if padding_len > 0:
            # unpad `hidden_states` because the calling function is expecting a length == input_ids.size(1)
            hidden_states = hidden_states[:, :-padding_len]
            if output_hidden_states:
                encoder_states = tuple(state[:, :-padding_len] for state in encoder_states)

            if output_attentions:
                all_attentions = tuple(state[:, :, :-padding_len, :] for state in all_attentions)

        if not return_dict:
            return tuple(
                v for v in [hidden_states, encoder_states, all_attentions, all_global_attentions] if v is not None
            )
        return LEDEncoderBaseModelOutput(
            last_hidden_state=hidden_states,
            hidden_states=encoder_states,
            attentions=all_attentions,
            global_attentions=all_global_attentions,
        )