def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        attention_mask: torch.LongTensor | None = None,
        token_type_ids: torch.LongTensor | None = None,
        position_ids: torch.LongTensor | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        visual_embeds: torch.FloatTensor | None = None,
        visual_attention_mask: torch.LongTensor | None = None,
        visual_token_type_ids: torch.LongTensor | None = None,
        image_text_alignment: torch.LongTensor | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple[torch.Tensor] | BaseModelOutputWithPooling:
        r"""
        visual_embeds (`torch.FloatTensor` of shape `(batch_size, visual_seq_length, visual_embedding_dim)`, *optional*):
            The embedded representation of the visual inputs, generally derived using using an object detector.
        visual_attention_mask (`torch.FloatTensor` of shape `(batch_size, visual_seq_length)`, *optional*):
            Mask to avoid performing attention on visual embeddings. Mask values selected in `[0, 1]`:

            - 1 for tokens that are **not masked**,
            - 0 for tokens that are **masked**.

            [What are attention masks?](../glossary#attention-mask)
        visual_token_type_ids (`torch.LongTensor` of shape `(batch_size, visual_seq_length)`, *optional*):
            Segment token indices to indicate different portions of the visual embeds.

            [What are token type IDs?](../glossary#token-type-ids) The authors of VisualBERT set the
            *visual_token_type_ids* to *1* for all tokens.
        image_text_alignment (`torch.LongTensor` of shape `(batch_size, visual_seq_length, alignment_number)`, *optional*):
            Image-Text alignment uses to decide the position IDs of the visual embeddings.

        Example:

        ```python
        # Assumption: *get_visual_embeddings(image)* gets the visual embeddings of the image.
        from transformers import AutoTokenizer, VisualBertModel
        import torch

        tokenizer = AutoTokenizer.from_pretrained("google-bert/bert-base-uncased")
        model = VisualBertModel.from_pretrained("uclanlp/visualbert-vqa-coco-pre")

        inputs = tokenizer("The capital of France is Paris.", return_tensors="pt")
        visual_embeds = get_visual_embeddings(image).unsqueeze(0)
        visual_token_type_ids = torch.ones(visual_embeds.shape[:-1], dtype=torch.long)
        visual_attention_mask = torch.ones(visual_embeds.shape[:-1], dtype=torch.float)

        inputs.update(
            {
                "visual_embeds": visual_embeds,
                "visual_token_type_ids": visual_token_type_ids,
                "visual_attention_mask": visual_attention_mask,
            }
        )

        outputs = model(**inputs)

        last_hidden_states = outputs.last_hidden_state
        ```"""

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

        batch_size, seq_length = input_shape
        device = input_ids.device if input_ids is not None else inputs_embeds.device

        if visual_embeds is not None:
            visual_input_shape = visual_embeds.size()[:-1]

        if attention_mask is None:
            attention_mask = torch.ones(input_shape, device=device)

        if visual_embeds is not None and visual_attention_mask is None:
            visual_attention_mask = torch.ones(visual_input_shape, device=device)

        # We can provide a self-attention mask of dimensions [batch_size, from_seq_length, to_seq_length]
        # ourselves in which case we just need to make it broadcastable to all heads.
        if visual_embeds is not None:
            combined_attention_mask = torch.cat((attention_mask, visual_attention_mask), dim=-1)
            extended_attention_mask: torch.Tensor = self.get_extended_attention_mask(
                combined_attention_mask, (batch_size, input_shape + visual_input_shape)
            )

        else:
            extended_attention_mask: torch.Tensor = self.get_extended_attention_mask(
                attention_mask, (batch_size, input_shape)
            )

        embedding_output = self.embeddings(
            input_ids=input_ids,
            position_ids=position_ids,
            token_type_ids=token_type_ids,
            inputs_embeds=inputs_embeds,
            visual_embeds=visual_embeds,
            visual_token_type_ids=visual_token_type_ids,
            image_text_alignment=image_text_alignment,
        )

        if self.bypass_transformer and visual_embeds is not None:
            text_length = input_ids.size(1)
            text_embedding_output = embedding_output[:, :text_length, :]
            visual_embedding_output = embedding_output[:, text_length:, :]

            text_extended_attention_mask = extended_attention_mask[:, :, text_length, :text_length]

            encoded_outputs = self.encoder(
                text_embedding_output,
                attention_mask=text_extended_attention_mask,
                output_attentions=output_attentions,
                output_hidden_states=output_hidden_states,
                return_dict=return_dict,
            )
            sequence_output = encoded_outputs[0]
            concatenated_input = torch.cat((sequence_output, visual_embedding_output), dim=1)
            sequence_output = self.additional_layer(concatenated_input, extended_attention_mask)
            pooled_output = self.pooler(sequence_output) if self.pooler is not None else None

        else:
            encoder_outputs = self.encoder(
                embedding_output,
                attention_mask=extended_attention_mask,
                output_attentions=output_attentions,
                output_hidden_states=output_hidden_states,
                return_dict=return_dict,
            )
            sequence_output = encoder_outputs[0]

            pooled_output = self.pooler(sequence_output) if self.pooler is not None else None

        if not return_dict:
            return (sequence_output, pooled_output) + encoder_outputs[1:]

        return BaseModelOutputWithPooling(
            last_hidden_state=sequence_output,
            pooler_output=pooled_output,
            hidden_states=encoder_outputs.hidden_states,
            attentions=encoder_outputs.attentions,
        )