def forward(
        self,
        input_ids: torch.Tensor | None = None,
        attention_mask: torch.Tensor | None = None,
        langs: torch.Tensor | None = None,
        token_type_ids: torch.Tensor | None = None,
        position_ids: torch.Tensor | None = None,
        lengths: torch.Tensor | None = None,
        cache: dict[str, torch.Tensor] | None = None,
        inputs_embeds: torch.Tensor | None = None,
        labels: torch.Tensor | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple | SequenceClassifierOutput:
        r"""
        langs (`torch.LongTensor` of shape `(batch_size, sequence_length)`, *optional*):
            A parallel sequence of tokens to be used to indicate the language of each token in the input. Indices are
            languages ids which can be obtained from the language names by using two conversion mappings provided in
            the configuration of the model (only provided for multilingual models). More precisely, the *language name
            to language id* mapping is in `model.config.lang2id` (which is a dictionary string to int) and the
            *language id to language name* mapping is in `model.config.id2lang` (dictionary int to string).

            See usage examples detailed in the [multilingual documentation](../multilingual).
        lengths (`torch.LongTensor` of shape `(batch_size,)`, *optional*):
            Length of each sentence that can be used to avoid performing attention on padding token indices. You can
            also use *attention_mask* for the same result (see above), kept here for compatibility. Indices selected in
            `[0, ..., input_ids.size(-1)]`.
        cache (`dict[str, torch.FloatTensor]`, *optional*):
            Instance of `EncoderDecoderCache` that contains precomputed KV states. Can be used to speed up sequential
            decoding.
        labels (`torch.LongTensor` of shape `(batch_size,)`, *optional*):
            Labels for computing the sequence classification/regression loss. Indices should be in `[0, ...,
            config.num_labels - 1]`. If `config.num_labels == 1` a regression loss is computed (Mean-Square loss), If
            `config.num_labels > 1` a classification loss is computed (Cross-Entropy).
        """
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        transformer_outputs = self.transformer(
            input_ids,
            attention_mask=attention_mask,
            langs=langs,
            token_type_ids=token_type_ids,
            position_ids=position_ids,
            lengths=lengths,
            cache=cache,
            inputs_embeds=inputs_embeds,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )

        output = transformer_outputs[0]
        logits = self.sequence_summary(output)

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
            output = (logits,) + transformer_outputs[1:]
            return ((loss,) + output) if loss is not None else output

        return SequenceClassifierOutput(
            loss=loss,
            logits=logits,
            hidden_states=transformer_outputs.hidden_states,
            attentions=transformer_outputs.attentions,
        )