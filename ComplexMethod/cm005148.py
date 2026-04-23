def forward(
        self,
        input_ids: torch.Tensor,
        encoder_hidden_states: torch.Tensor,
        encoder_padding_mask: torch.Tensor,
        decoder_padding_mask: torch.Tensor,
        decoder_causal_mask: torch.Tensor,
        inputs_embeds: torch.Tensor | None = None,
        past_key_values: Cache | None = None,
        use_cache: bool | None = False,
        output_attentions: bool | None = False,
        output_hidden_states: bool | None = False,
        return_dict: bool | None = True,
        **kwargs,
    ):
        """
        Includes several features from "Jointly Learning to Align and Translate with Transformer Models" (Garg et al.,
        EMNLP 2019).

        Args:
            input_ids (`torch.LongTensor` of shape `(batch, tgt_len)`):
                previous decoder outputs for teacher forcing
            encoder_hidden_states: output from the encoder, used for
                encoder-side attention
            encoder_padding_mask: for ignoring pad tokens
            past_key_values (dict or None): dictionary used for storing state during generation

        Returns:
            BaseModelOutputWithPast or tuple:

                - the decoder's features of shape *(batch, tgt_len, embed_dim)*
                - the cache
                - hidden states
                - attentions
        """
        # check attention mask and invert
        if encoder_padding_mask is not None:
            encoder_padding_mask = invert_mask(encoder_padding_mask)

        if input_ids is not None and inputs_embeds is not None:
            raise ValueError("You cannot specify both decoder_input_ids and decoder_inputs_embeds at the same time")
        elif input_ids is not None:
            # embed positions
            positions = self.embed_positions(input_ids)
            if use_cache:
                input_ids = input_ids[:, -1:]
                positions = positions[:, -1:]  # happens after we embed them
            x = self.embed_tokens(input_ids) * self.embed_scale
        elif inputs_embeds is not None:
            # We assume zeros hidden states correspond to padding tokens
            # and create `position_ids` where inputs_embeds[:, :, 0] == 0
            position_ids = inputs_embeds[:, :, 0].masked_fill(
                inputs_embeds[:, :, 0].eq(0), self.embed_positions.padding_idx
            )
            positions = self.embed_positions(position_ids)
            x = inputs_embeds * self.embed_scale
        else:
            raise ValueError("You have to specify either decoder_input_ids or decoder_inputs_embeds")

        x += positions
        x = nn.functional.dropout(x, p=self.dropout, training=self.training)

        # Convert to FSMT output format: (BS, seq_len, model_dim) -> (seq_len, BS, model_dim)
        x = x.transpose(0, 1)
        encoder_hidden_states = encoder_hidden_states.transpose(0, 1)

        # decoder layers
        all_hidden_states = () if output_hidden_states else None
        all_self_attns = () if output_attentions else None
        all_cross_attns = () if output_attentions else None

        for idx, decoder_layer in enumerate(self.layers):
            # add LayerDrop (see https://huggingface.co/papers/1909.11556 for description)
            if output_hidden_states:
                x = x.transpose(0, 1)
                all_hidden_states += (x,)
                x = x.transpose(0, 1)
            if self.training:
                dropout_probability = torch.rand([])
                if dropout_probability < self.layerdrop:
                    continue

            x, layer_self_attn, layer_cross_attn = decoder_layer(
                x,
                encoder_hidden_states,
                encoder_attn_mask=encoder_padding_mask,
                decoder_padding_mask=decoder_padding_mask,
                layer_state=past_key_values,
                causal_mask=decoder_causal_mask,
                output_attentions=output_attentions,
            )

            if output_attentions:
                all_self_attns += (layer_self_attn,)
                all_cross_attns += (layer_cross_attn,)

        # add hidden states from the last decoder layer
        if output_hidden_states:
            x = x.transpose(0, 1)
            all_hidden_states += (x,)
            x = x.transpose(0, 1)

        # Convert to standard output format: (seq_len, BS, model_dim) -> (BS, seq_len, model_dim)
        x = x.transpose(0, 1)
        encoder_hidden_states = encoder_hidden_states.transpose(0, 1)

        x = self.output_projection(x)

        if not return_dict:
            return tuple(
                v for v in [x, past_key_values, all_hidden_states, all_self_attns, all_cross_attns] if v is not None
            )
        return BaseModelOutputWithPastAndCrossAttentions(
            last_hidden_state=x,
            past_key_values=past_key_values,
            hidden_states=all_hidden_states,
            attentions=all_self_attns,
            cross_attentions=all_cross_attns,
        )