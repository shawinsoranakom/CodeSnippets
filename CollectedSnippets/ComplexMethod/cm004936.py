def forward(
        self,
        input_ids: torch.Tensor | None = None,
        position_ids: torch.Tensor | None = None,
        attention_mask: torch.Tensor | None = None,
        inputs_embeds: torch.Tensor | None = None,
        num_hashes: int | None = None,
        labels: torch.Tensor | None = None,
        output_hidden_states: bool | None = None,
        output_attentions: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple | SequenceClassifierOutput:
        r"""
        input_ids (`torch.LongTensor` of shape `(batch_size, sequence_length)`):
            Indices of input sequence tokens in the vocabulary. During training the input_ids sequence_length has to be
            a multiple of the relevant model's chunk lengths (lsh's, local's or both). During evaluation, the indices
            are automatically padded to be a multiple of the chunk length.

            Indices can be obtained using [`AutoTokenizer`]. See [`PreTrainedTokenizer.encode`] and
            [`PreTrainedTokenizer.__call__`] for details.

            [What are input IDs?](../glossary#input-ids)
        num_hashes (`int`, *optional*):
            The number of hashing rounds that should be performed during bucketing. Setting this argument overwrites
            the default defined in `config.num_hashes`.

            For more information, see `num_hashes` in [`ReformerConfig`].
        labels (`torch.LongTensor` of shape `(batch_size,)`, *optional*):
            Labels for computing the sequence classification/regression loss. Indices should be in `[0, ...,
            config.num_labels - 1]`. If `config.num_labels == 1` a regression loss is computed (Mean-Square loss), If
            `config.num_labels > 1` a classification loss is computed (Cross-Entropy).

        Example of single-label classification:

        ```python
        >>> import torch
        >>> from transformers import AutoTokenizer, ReformerForSequenceClassification

        >>> tokenizer = AutoTokenizer.from_pretrained("google/reformer-crime-and-punishment")
        >>> model = ReformerForSequenceClassification.from_pretrained("google/reformer-crime-and-punishment")

        >>> inputs = tokenizer("Hello, my dog is cute", return_tensors="pt")

        >>> with torch.no_grad():
        ...     logits = model(**inputs).logits

        >>> predicted_class_id = logits.argmax().item()
        >>> label = model.config.id2label[predicted_class_id]
        ```

        ```python
        >>> # To train a model on `num_labels` classes, you can pass `num_labels=num_labels` to `.from_pretrained(...)`
        >>> num_labels = len(model.config.id2label)
        >>> model = ReformerForSequenceClassification.from_pretrained(
        ...     "google/reformer-crime-and-punishment", num_labels=num_labels
        ... )

        >>> labels = torch.tensor(1)
        >>> loss = model(**inputs, labels=labels).loss
        ```
        """
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        outputs = self.reformer(
            input_ids,
            position_ids=position_ids,
            attention_mask=attention_mask,
            inputs_embeds=inputs_embeds,
            num_hashes=num_hashes,
            output_hidden_states=output_hidden_states,
            output_attentions=output_attentions,
            return_dict=return_dict,
        )

        sequence_output = outputs[0]
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

        if not return_dict:
            output = (logits,) + outputs[2:]
            return ((loss,) + output) if loss is not None else output

        return SequenceClassifierOutput(
            loss=loss,
            logits=logits,
            hidden_states=outputs.hidden_states,
            attentions=outputs.attentions,
        )