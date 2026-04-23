def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        visual_feats: torch.FloatTensor | None = None,
        visual_pos: torch.FloatTensor | None = None,
        attention_mask: torch.FloatTensor | None = None,
        visual_attention_mask: torch.FloatTensor | None = None,
        token_type_ids: torch.LongTensor | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> LxmertModelOutput | tuple[torch.FloatTensor]:
        r"""
        visual_feats (`torch.FloatTensor` of shape `(batch_size, num_visual_features, visual_feat_dim)`):
            This input represents visual features. They ROI pooled object features from bounding boxes using a
            faster-RCNN model)

            These are currently not provided by the transformers library.
        visual_pos (`torch.FloatTensor` of shape `(batch_size, num_visual_features, visual_pos_dim)`):
            This input represents spatial features corresponding to their relative (via index) visual features. The
            pre-trained LXMERT model expects these spatial features to be normalized bounding boxes on a scale of 0 to
            1.

            These are currently not provided by the transformers library.
        visual_attention_mask (`torch.FloatTensor` of shape `(batch_size, sequence_length)`, *optional*):
            Mask to avoid performing attention on padding token indices. Mask values selected in `[0, 1]`:

            - 1 for tokens that are **not masked**,
            - 0 for tokens that are **masked**.

            [What are attention masks?](../glossary#attention-mask)
        """
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        if input_ids is not None and inputs_embeds is not None:
            raise ValueError("You cannot specify both input_ids and inputs_embeds at the same time")
        elif input_ids is not None:
            self.warn_if_padding_and_no_attention_mask(input_ids, attention_mask)
            input_shape = input_ids.size()
        elif inputs_embeds is not None:
            input_shape = inputs_embeds.size()[:-1]
        else:
            raise ValueError("You have to specify either input_ids or inputs_embeds")

        if visual_feats is None:
            raise ValueError("`visual_feats` cannot be `None`")
        if visual_pos is None:
            raise ValueError("`visual_pos` cannot be `None`")

        device = input_ids.device if input_ids is not None else inputs_embeds.device

        if attention_mask is None:
            attention_mask = torch.ones(input_shape, device=device)
        if token_type_ids is None:
            token_type_ids = torch.zeros(input_shape, dtype=torch.long, device=device)

        # We create a 3D attention mask from a 2D tensor mask.
        # Sizes are [batch_size, 1, 1, to_seq_length]
        # So we can broadcast to [batch_size, num_heads, from_seq_length, to_seq_length]
        # this attention mask is more simple than the triangular masking of causal attention
        # used in OpenAI GPT, we just need to prepare the broadcast dimension here.
        extended_attention_mask = attention_mask.unsqueeze(1).unsqueeze(2)

        # Since attention_mask is 1.0 for positions we want to attend and 0.0 for
        # masked positions, this operation will create a tensor which is 0.0 for
        # positions we want to attend and the dtype's smallest value for masked positions.
        # Since we are adding it to the raw scores before the softmax, this is
        # effectively the same as removing these entirely.
        extended_attention_mask = extended_attention_mask.to(dtype=self.dtype)
        extended_attention_mask = (1.0 - extended_attention_mask) * torch.finfo(self.dtype).min

        # Process the visual attention mask
        if visual_attention_mask is not None:
            extended_visual_attention_mask = visual_attention_mask.unsqueeze(1).unsqueeze(2)
            extended_visual_attention_mask = extended_visual_attention_mask.to(dtype=self.dtype)
            extended_visual_attention_mask = (1.0 - extended_visual_attention_mask) * torch.finfo(self.dtype).min
        else:
            extended_visual_attention_mask = None

        # Positional Word Embeddings
        embedding_output = self.embeddings(input_ids, token_type_ids, inputs_embeds)

        # Run Lxmert encoder
        encoder_outputs = self.encoder(
            embedding_output,
            extended_attention_mask,
            visual_feats=visual_feats,
            visual_pos=visual_pos,
            visual_attention_mask=extended_visual_attention_mask,
            output_attentions=output_attentions,
        )

        visual_encoder_outputs, lang_encoder_outputs = encoder_outputs[:2]
        vision_hidden_states = visual_encoder_outputs[0]
        language_hidden_states = lang_encoder_outputs[0]

        all_attentions = ()
        if output_attentions:
            language_attentions = lang_encoder_outputs[1]
            vision_attentions = visual_encoder_outputs[1]
            cross_encoder_attentions = encoder_outputs[2]
            all_attentions = (
                language_attentions,
                vision_attentions,
                cross_encoder_attentions,
            )

        hidden_states = (language_hidden_states, vision_hidden_states) if output_hidden_states else ()

        visual_output = vision_hidden_states[-1]
        lang_output = language_hidden_states[-1]
        pooled_output = self.pooler(lang_output)

        if not return_dict:
            return (lang_output, visual_output, pooled_output) + hidden_states + all_attentions

        return LxmertModelOutput(
            pooled_output=pooled_output,
            language_output=lang_output,
            vision_output=visual_output,
            language_hidden_states=language_hidden_states if output_hidden_states else None,
            vision_hidden_states=vision_hidden_states if output_hidden_states else None,
            language_attentions=language_attentions if output_attentions else None,
            vision_attentions=vision_attentions if output_attentions else None,
            cross_encoder_attentions=cross_encoder_attentions if output_attentions else None,
        )