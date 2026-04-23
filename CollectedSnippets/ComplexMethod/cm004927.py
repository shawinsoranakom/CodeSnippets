def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        attention_mask: torch.Tensor | None = None,
        position_ids: torch.LongTensor | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        labels: torch.LongTensor | None = None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> tuple[torch.Tensor] | SequenceClassifierOutput:
        encoder_output = self.model(
            input_ids,
            attention_mask=attention_mask,
            position_ids=position_ids,
            inputs_embeds=inputs_embeds,
            **kwargs,
        )
        last_hidden_state = encoder_output[0]

        if self.classifier_pooling in ["bos", "mean"]:
            if self.classifier_pooling == "bos":
                pooled_output = last_hidden_state[:, 0]

            elif self.classifier_pooling == "mean":
                if attention_mask is None:
                    pooled_output = last_hidden_state.mean(dim=1)
                else:
                    attention_mask = attention_mask.to(last_hidden_state.device)
                    pooled_output = (last_hidden_state * attention_mask.unsqueeze(-1)).sum(dim=1)
                    pooled_output /= attention_mask.sum(dim=1, keepdim=True)

            pooled_output = self.dense(pooled_output)
            pooled_output = self.activation(pooled_output)
            logits = self.classifier(pooled_output)

        elif self.classifier_pooling == "late":
            x = self.dense(last_hidden_state)
            x = self.activation(x)
            logits = self.classifier(x)
            if attention_mask is None:
                logits = logits.mean(dim=1)
            else:
                attention_mask = attention_mask.to(logits.device)
                logits = (logits * attention_mask.unsqueeze(-1)).sum(dim=1)
                logits /= attention_mask.sum(dim=1, keepdim=True)

        loss = None
        if labels is not None:
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

        return SequenceClassifierOutput(
            loss=loss,
            logits=logits,
            hidden_states=encoder_output.hidden_states,
            attentions=encoder_output.attentions,
        )