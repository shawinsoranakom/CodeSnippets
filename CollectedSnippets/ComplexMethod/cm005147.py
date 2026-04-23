def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor | None = None,
        inputs_embeds: torch.Tensor | None = None,
        output_attentions: bool = False,
        output_hidden_states: bool = False,
        return_dict: bool = True,
    ):
        """
        Args:
            input_ids (`torch.LongTensor`): tokens in the source language of shape
                *(batch, src_len)*
            attention_mask (`torch.LongTensor`): indicating which indices are padding tokens
            inputs_embeds (`torch.FloatTensor`):
                embedding vectors of shape *(batch, src_len, embed_dim)*

        Returns:
            BaseModelOutput or Tuple comprised of:

                - **x** (`torch.Tensor`): the last encoder layer's output of shape *(src_len, batch, embed_dim)*
                - **encoder_states** (`Tuple(torch.FloatTensor)`): all intermediate hidden states of shape *(src_len,
                  batch, embed_dim)*. Only populated if *output_hidden_states:* is True.
                - **all_attentions** (`Tuple(torch.FloatTensor)`): Attention weights for each layer.
                During training might not be of length n_layers because of layer dropout.
        """
        # check attention mask and invert
        if attention_mask is not None:
            attention_mask = invert_mask(attention_mask)

        if input_ids is not None and inputs_embeds is not None:
            raise ValueError("You cannot specify both input_ids and inputs_embeds at the same time")
        elif input_ids is not None:
            inputs_embeds = self.embed_tokens(input_ids) * self.embed_scale
            embed_pos = self.embed_positions(input_ids)
        elif inputs_embeds is not None:
            inputs_embeds = inputs_embeds * self.embed_scale

            # We assume zeros hidden states correspond to padding tokens
            # and create `position_ids` where inputs_embeds[:, :, 0] == 0
            position_ids = inputs_embeds[:, :, 0].masked_fill(
                inputs_embeds[:, :, 0].eq(0), self.embed_positions.padding_idx
            )

            embed_pos = self.embed_positions(position_ids)
        else:
            raise ValueError("You have to specify either input_ids or inputs_embeds")

        x = inputs_embeds + embed_pos
        x = nn.functional.dropout(x, p=self.dropout, training=self.training)

        # B x T x C -> T x B x C
        x = x.transpose(0, 1)

        encoder_states = () if output_hidden_states else None
        all_attentions = () if output_attentions else None
        for idx, encoder_layer in enumerate(self.layers):
            if output_hidden_states:
                x = x.transpose(0, 1)  # T x B x C -> B x T x C
                encoder_states += (x,)
                x = x.transpose(0, 1)  # B x T x C -> T x B x C
            # add LayerDrop (see https://huggingface.co/papers/1909.11556 for description)
            dropout_probability = torch.rand([])
            if self.training and (dropout_probability < self.layerdrop):  # skip the layer
                attn = None
            else:
                x, attn = encoder_layer(
                    x,
                    attention_mask,
                    output_attentions=output_attentions,
                )

            if output_attentions:
                all_attentions = all_attentions + (attn,)

        # T x B x C -> B x T x C
        x = x.transpose(0, 1)

        if output_hidden_states:
            encoder_states += (x,)

        if not return_dict:
            return tuple(v for v in [x, encoder_states, all_attentions] if v is not None)
        return BaseModelOutput(last_hidden_state=x, hidden_states=encoder_states, attentions=all_attentions)