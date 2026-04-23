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
    ) -> tuple | LukeSequenceClassifierOutput:
        r"""
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
        labels (`torch.LongTensor` of shape `(batch_size,)`, *optional*):
            Labels for computing the sequence classification/regression loss. Indices should be in `[0, ...,
            config.num_labels - 1]`. If `config.num_labels == 1` a regression loss is computed (Mean-Square loss), If
            `config.num_labels > 1` a classification loss is computed (Cross-Entropy).
        """
        return_dict = return_dict if return_dict is not None else self.config.return_dict

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

        loss = None
        if labels is not None:
            # move labels to correct device
            labels = labels.to(logits.device)
            if self.config.problem_type is None:
                if self.num_labels == 1:
                    self.config.problem_type = "regression"
                elif self.num_labels > 1 and (labels.dtype == torch.long or labels.dtype == torch.int):
                    self.config.problem_type = "single_label_classification"
                else:
                    self.config.problem_type = "multi_label_classification"

            if self.config.problem_type == "regression":
                loss_fct = MSELoss()
                if self.num_labels == 1:
                    loss = loss_fct(logits.squeeze(), labels.squeeze())
                else:
                    loss = loss_fct(logits, labels)
            elif self.config.problem_type == "single_label_classification":
                loss_fct = CrossEntropyLoss()
                loss = loss_fct(logits.view(-1, self.num_labels), labels.view(-1))
            elif self.config.problem_type == "multi_label_classification":
                loss_fct = BCEWithLogitsLoss()
                loss = loss_fct(logits, labels)

        if not return_dict:
            return tuple(
                v
                for v in [loss, logits, outputs.hidden_states, outputs.entity_hidden_states, outputs.attentions]
                if v is not None
            )

        return LukeSequenceClassifierOutput(
            loss=loss,
            logits=logits,
            hidden_states=outputs.hidden_states,
            entity_hidden_states=outputs.entity_hidden_states,
            attentions=outputs.attentions,
        )