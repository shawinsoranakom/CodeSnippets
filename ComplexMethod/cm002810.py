def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        attention_mask: torch.FloatTensor | None = None,
        token_type_ids: torch.LongTensor | None = None,
        position_ids: torch.LongTensor | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        labels: torch.LongTensor | None = None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> SequenceClassifierOutput:
        r"""
        labels (`torch.LongTensor` of shape `(batch_size,)`, *optional*):
            Labels for computing the sequence classification/regression loss. Indices should be in `[0, ...,
            config.num_labels - 1]`. If `config.num_labels == 1` a regression loss is computed (Mean-Square loss), If
            `config.num_labels > 1` a classification loss is computed (Cross-Entropy).

        Example:

        ```python
        >>> import torch
        >>> from transformers import AutoTokenizer, BigBirdForSequenceClassification
        >>> from datasets import load_dataset

        >>> tokenizer = AutoTokenizer.from_pretrained("l-yohai/bigbird-roberta-base-mnli")
        >>> model = BigBirdForSequenceClassification.from_pretrained("l-yohai/bigbird-roberta-base-mnli")
        >>> squad_ds = load_dataset("rajpurkar/squad_v2", split="train")  # doctest: +IGNORE_RESULT

        >>> LONG_ARTICLE = squad_ds[81514]["context"]
        >>> inputs = tokenizer(LONG_ARTICLE, return_tensors="pt")
        >>> # long input article
        >>> list(inputs["input_ids"].shape)
        [1, 919]

        >>> with torch.no_grad():
        ...     logits = model(**inputs).logits
        >>> predicted_class_id = logits.argmax().item()
        >>> model.config.id2label[predicted_class_id]
        'LABEL_0'
        ```

        ```python
        >>> num_labels = len(model.config.id2label)
        >>> model = BigBirdForSequenceClassification.from_pretrained(
        ...     "l-yohai/bigbird-roberta-base-mnli", num_labels=num_labels
        ... )
        >>> labels = torch.tensor(1)
        >>> loss = model(**inputs, labels=labels).loss
        >>> round(loss.item(), 2)
        1.13
        ```
        """
        outputs: BaseModelOutputWithPoolingAndCrossAttentions = self.bert(
            input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            position_ids=position_ids,
            inputs_embeds=inputs_embeds,
            **kwargs,
        )

        sequence_output = outputs.last_hidden_state
        logits = self.classifier(sequence_output)

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

        return SequenceClassifierOutput(
            loss=loss,
            logits=logits,
            hidden_states=outputs.hidden_states,
            attentions=outputs.attentions,
        )