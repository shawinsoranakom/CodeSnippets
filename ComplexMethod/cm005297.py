def forward(
        self,
        inputs: torch.Tensor | None = None,
        attention_mask: torch.Tensor | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        labels: torch.Tensor | None = None,
        return_dict: bool | None = None,
        input_ids: torch.Tensor | None = None,
        **kwargs,
    ) -> tuple | PerceiverClassifierOutput:
        r"""
        inputs (`torch.FloatTensor`):
            Inputs to the perceiver. Can be anything: images, text, audio, video, etc.
        labels (`torch.LongTensor` of shape `(batch_size,)`, *optional*):
            Labels for computing the classification/regression loss. Indices should be in `[0, ..., config.num_labels -
            1]`. If `config.num_labels == 1` a regression loss is computed (Mean-Square loss), If `config.num_labels >
            1` a classification loss is computed (Cross-Entropy).

        Examples:

        ```python
        >>> from transformers import AutoTokenizer, PerceiverForSequenceClassification

        >>> tokenizer = AutoTokenizer.from_pretrained("deepmind/language-perceiver")
        >>> model = PerceiverForSequenceClassification.from_pretrained("deepmind/language-perceiver")

        >>> text = "hello world"
        >>> inputs = tokenizer(text, return_tensors="pt").input_ids
        >>> outputs = model(inputs=inputs)
        >>> logits = outputs.logits
        >>> list(logits.shape)
        [1, 2]
        ```"""
        if inputs is not None and input_ids is not None:
            raise ValueError("You cannot use both `inputs` and `input_ids`")
        elif inputs is None and input_ids is not None:
            inputs = input_ids

        return_dict = return_dict if return_dict is not None else self.config.return_dict

        outputs = self.perceiver(
            inputs=inputs,
            attention_mask=attention_mask,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )

        logits = outputs.logits if return_dict else outputs[0]

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

        return PerceiverClassifierOutput(
            loss=loss,
            logits=logits,
            hidden_states=outputs.hidden_states,
            attentions=outputs.attentions,
            cross_attentions=outputs.cross_attentions,
        )