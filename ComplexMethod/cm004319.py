def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        attention_mask: torch.FloatTensor | None = None,
        token_type_ids: torch.LongTensor | None = None,
        position_ids: torch.LongTensor | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        labels: torch.LongTensor | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple[torch.Tensor] | SequenceClassifierOutput:
        r"""
        token_type_ids (`torch.LongTensor` of shape `(batch_size, sequence_length, 7)`, *optional*):
            Token indices that encode tabular structure. Indices can be obtained using [`AutoTokenizer`]. See this
            class for more info.

            [What are token type IDs?](../glossary#token-type-ids)
        position_ids (`torch.LongTensor` of shape `(batch_size, sequence_length)`, *optional*):
            Indices of positions of each input sequence tokens in the position embeddings. If
            `reset_position_index_per_cell` of [`TapasConfig`] is set to `True`, relative position embeddings will be
            used. Selected in the range `[0, config.max_position_embeddings - 1]`.

            [What are position IDs?](../glossary#position-ids)
        labels (`torch.LongTensor` of shape `(batch_size,)`, *optional*):
            Labels for computing the sequence classification/regression loss. Indices should be in `[0, ...,
            config.num_labels - 1]`. If `config.num_labels == 1` a regression loss is computed (Mean-Square loss), If
            `config.num_labels > 1` a classification loss is computed (Cross-Entropy). Note: this is called
            "classification_class_index" in the original implementation.

        Examples:

        ```python
        >>> from transformers import AutoTokenizer, TapasForSequenceClassification
        >>> import torch
        >>> import pandas as pd

        >>> tokenizer = AutoTokenizer.from_pretrained("google/tapas-base-finetuned-tabfact")
        >>> model = TapasForSequenceClassification.from_pretrained("google/tapas-base-finetuned-tabfact")

        >>> data = {
        ...     "Actors": ["Brad Pitt", "Leonardo Di Caprio", "George Clooney"],
        ...     "Age": ["56", "45", "59"],
        ...     "Number of movies": ["87", "53", "69"],
        ... }
        >>> table = pd.DataFrame.from_dict(data)
        >>> queries = [
        ...     "There is only one actor who is 45 years old",
        ...     "There are 3 actors which played in more than 60 movies",
        ... ]

        >>> inputs = tokenizer(table=table, queries=queries, padding="max_length", return_tensors="pt")
        >>> labels = torch.tensor([1, 0])  # 1 means entailed, 0 means refuted

        >>> outputs = model(**inputs, labels=labels)
        >>> loss = outputs.loss
        >>> logits = outputs.logits
        ```"""
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        outputs = self.tapas(
            input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            position_ids=position_ids,
            inputs_embeds=inputs_embeds,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )

        pooled_output = outputs[1]

        pooled_output = self.dropout(pooled_output)
        logits = self.classifier(pooled_output)

        loss = None
        if labels is not None:
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
            output = (logits,) + outputs[2:]
            return ((loss,) + output) if loss is not None else output

        return SequenceClassifierOutput(
            loss=loss,
            logits=logits,
            hidden_states=outputs.hidden_states,
            attentions=outputs.attentions,
        )