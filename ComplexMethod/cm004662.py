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
        labels: torch.LongTensor | None = None,
        **kwargs,
    ) -> tuple[torch.Tensor] | MultipleChoiceModelOutput:
        r"""
        input_ids (`torch.LongTensor` of shape `(batch_size, num_choices, sequence_length)`):
            Indices of input sequence tokens in the vocabulary.

            Indices can be obtained using [`AutoTokenizer`]. See [`PreTrainedTokenizer.encode`] and
            [`PreTrainedTokenizer.__call__`] for details.

            [What are input IDs?](../glossary#input-ids)
        token_type_ids (`torch.LongTensor` of shape `(batch_size, num_choices, sequence_length)`, *optional*):
            Segment token indices to indicate first and second portions of the inputs. Indices are selected in `[0,
            1]`:

            - 0 corresponds to a *sentence A* token,
            - 1 corresponds to a *sentence B* token.

            [What are token type IDs?](../glossary#token-type-ids)
        position_ids (`torch.LongTensor` of shape `(batch_size, num_choices, sequence_length)`, *optional*):
            Indices of positions of each input sequence tokens in the position embeddings. Selected in the range `[0,
            config.max_position_embeddings - 1]`.

            [What are position IDs?](../glossary#position-ids)
        inputs_embeds (`torch.FloatTensor` of shape `(batch_size, num_choices, sequence_length, hidden_size)`, *optional*):
            Optionally, instead of passing `input_ids` you can choose to directly pass an embedded representation. This
            is useful if you want more control over how to convert `input_ids` indices into associated vectors than the
            model's internal embedding lookup matrix.
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
        labels (`torch.LongTensor` of shape `(batch_size,)`, *optional*):
            Labels for computing the multiple choice classification loss. Indices should be in `[0, ...,
            num_choices-1]` where `num_choices` is the size of the second dimension of the input tensors. (See
            `input_ids` above)

        Example:

        ```python
        # Assumption: *get_visual_embeddings(image)* gets the visual embeddings of the image in the batch.
        from transformers import AutoTokenizer, VisualBertForMultipleChoice
        import torch

        tokenizer = AutoTokenizer.from_pretrained("google-bert/bert-base-uncased")
        model = VisualBertForMultipleChoice.from_pretrained("uclanlp/visualbert-vcr")

        prompt = "In Italy, pizza served in formal settings, such as at a restaurant, is presented unsliced."
        choice0 = "It is eaten with a fork and a knife."
        choice1 = "It is eaten while held in the hand."

        visual_embeds = get_visual_embeddings(image)
        # (batch_size, num_choices, visual_seq_length, visual_embedding_dim)
        visual_embeds = visual_embeds.expand(1, 2, *visual_embeds.shape)
        visual_token_type_ids = torch.ones(visual_embeds.shape[:-1], dtype=torch.long)
        visual_attention_mask = torch.ones(visual_embeds.shape[:-1], dtype=torch.float)

        labels = torch.tensor(0).unsqueeze(0)  # choice0 is correct (according to Wikipedia ;)), batch size 1

        encoding = tokenizer([[prompt, prompt], [choice0, choice1]], return_tensors="pt", padding=True)
        # batch size is 1
        inputs_dict = {k: v.unsqueeze(0) for k, v in encoding.items()}
        inputs_dict.update(
            {
                "visual_embeds": visual_embeds,
                "visual_attention_mask": visual_attention_mask,
                "visual_token_type_ids": visual_token_type_ids,
                "labels": labels,
            }
        )
        outputs = model(**inputs_dict)

        loss = outputs.loss
        logits = outputs.logits
        ```"""
        return_dict = return_dict if return_dict is not None else self.config.return_dict
        num_choices = input_ids.shape[1] if input_ids is not None else inputs_embeds.shape[1]

        input_ids = input_ids.view(-1, input_ids.size(-1)) if input_ids is not None else None
        attention_mask = attention_mask.view(-1, attention_mask.size(-1)) if attention_mask is not None else None
        token_type_ids = token_type_ids.view(-1, token_type_ids.size(-1)) if token_type_ids is not None else None
        position_ids = position_ids.view(-1, position_ids.size(-1)) if position_ids is not None else None
        inputs_embeds = (
            inputs_embeds.view(-1, inputs_embeds.size(-2), inputs_embeds.size(-1))
            if inputs_embeds is not None
            else None
        )

        visual_embeds = (
            visual_embeds.view(-1, visual_embeds.size(-2), visual_embeds.size(-1))
            if visual_embeds is not None
            else None
        )
        visual_attention_mask = (
            visual_attention_mask.view(-1, visual_attention_mask.size(-1))
            if visual_attention_mask is not None
            else None
        )
        visual_token_type_ids = (
            visual_token_type_ids.view(-1, visual_token_type_ids.size(-1))
            if visual_token_type_ids is not None
            else None
        )

        outputs = self.visual_bert(
            input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            position_ids=position_ids,
            inputs_embeds=inputs_embeds,
            visual_embeds=visual_embeds,
            visual_attention_mask=visual_attention_mask,
            visual_token_type_ids=visual_token_type_ids,
            image_text_alignment=image_text_alignment,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )

        _, pooled_output = outputs[0], outputs[1]

        pooled_output = self.dropout(pooled_output)
        logits = self.cls(pooled_output)
        reshaped_logits = logits.view(-1, num_choices)

        loss = None
        if labels is not None:
            loss_fct = CrossEntropyLoss()
            loss = loss_fct(reshaped_logits, labels)

        if not return_dict:
            output = (reshaped_logits,) + outputs[2:]
            return ((loss,) + output) if loss is not None else output

        return MultipleChoiceModelOutput(
            loss=loss,
            logits=reshaped_logits,
            hidden_states=outputs.hidden_states,
            attentions=outputs.attentions,
        )