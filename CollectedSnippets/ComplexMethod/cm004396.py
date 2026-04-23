def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        attention_mask: torch.FloatTensor | None = None,
        token_type_ids: torch.LongTensor | None = None,
        position_ids: torch.LongTensor | None = None,
        entity_ids: torch.LongTensor | None = None,
        entity_attention_mask: torch.FloatTensor | None = None,
        entity_token_type_ids: torch.LongTensor | None = None,
        entity_position_ids: torch.LongTensor | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        labels: torch.FloatTensor | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple | LukeMultipleChoiceModelOutput:
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
        entity_ids (`torch.LongTensor` of shape `(batch_size, entity_length)`):
            Indices of entity tokens in the entity vocabulary.

            Indices can be obtained using [`AutoTokenizer`]. See [`PreTrainedTokenizer.encode`] and
            [`PreTrainedTokenizer.__call__`] for details.
        entity_attention_mask (`torch.FloatTensor` of shape `(batch_size, entity_length)`, *optional*):
            Mask to avoid performing attention on padding entity token indices. Mask values selected in `[0, 1]`:

            - 1 for entity tokens that are **not masked**,
            - 0 for entity tokens that are **masked**.
        entity_token_type_ids (`torch.LongTensor` of shape `(batch_size, entity_length)`, *optional*):
            Segment token indices to indicate first and second portions of the entity token inputs. Indices are
            selected in `[0, 1]`:

            - 0 corresponds to a *portion A* entity token,
            - 1 corresponds to a *portion B* entity token.
        entity_position_ids (`torch.LongTensor` of shape `(batch_size, entity_length, max_mention_length)`, *optional*):
            Indices of positions of each input entity in the position embeddings. Selected in the range `[0,
            config.max_position_embeddings - 1]`.
        inputs_embeds (`torch.FloatTensor` of shape `(batch_size, num_choices, sequence_length, hidden_size)`, *optional*):
            Optionally, instead of passing `input_ids` you can choose to directly pass an embedded representation. This
            is useful if you want more control over how to convert `input_ids` indices into associated vectors than the
            model's internal embedding lookup matrix.
        labels (`torch.LongTensor` of shape `(batch_size,)`, *optional*):
            Labels for computing the multiple choice classification loss. Indices should be in `[0, ...,
            num_choices-1]` where `num_choices` is the size of the second dimension of the input tensors. (See
            `input_ids` above)
        """
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

        entity_ids = entity_ids.view(-1, entity_ids.size(-1)) if entity_ids is not None else None
        entity_attention_mask = (
            entity_attention_mask.view(-1, entity_attention_mask.size(-1))
            if entity_attention_mask is not None
            else None
        )
        entity_token_type_ids = (
            entity_token_type_ids.view(-1, entity_token_type_ids.size(-1))
            if entity_token_type_ids is not None
            else None
        )
        entity_position_ids = (
            entity_position_ids.view(-1, entity_position_ids.size(-2), entity_position_ids.size(-1))
            if entity_position_ids is not None
            else None
        )

        outputs = self.luke(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            position_ids=position_ids,
            entity_ids=entity_ids,
            entity_attention_mask=entity_attention_mask,
            entity_token_type_ids=entity_token_type_ids,
            entity_position_ids=entity_position_ids,
            inputs_embeds=inputs_embeds,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=True,
        )

        pooled_output = outputs.pooler_output

        pooled_output = self.dropout(pooled_output)
        logits = self.classifier(pooled_output)
        reshaped_logits = logits.view(-1, num_choices)

        loss = None
        if labels is not None:
            # move labels to correct device
            labels = labels.to(reshaped_logits.device)
            loss_fct = CrossEntropyLoss()
            loss = loss_fct(reshaped_logits, labels)

        if not return_dict:
            return tuple(
                v
                for v in [
                    loss,
                    reshaped_logits,
                    outputs.hidden_states,
                    outputs.entity_hidden_states,
                    outputs.attentions,
                ]
                if v is not None
            )

        return LukeMultipleChoiceModelOutput(
            loss=loss,
            logits=reshaped_logits,
            hidden_states=outputs.hidden_states,
            entity_hidden_states=outputs.entity_hidden_states,
            attentions=outputs.attentions,
        )