def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        attention_mask: torch.Tensor | None = None,
        position_ids: torch.Tensor | None = None,
        inputs_embeds: torch.Tensor | None = None,
        labels: torch.Tensor | None = None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> tuple[torch.Tensor] | MultipleChoiceModelOutput:
        r"""
        labels (`torch.LongTensor` of shape `(batch_size,)`, *optional*):
            Labels for computing the multiple choice classification loss. Indices should be in `[0, ...,
            num_choices-1]` where `num_choices` is the size of the second dimension of the input tensors.
        """
        num_choices = input_ids.shape[1] if input_ids is not None else inputs_embeds.shape[1]

        input_ids = input_ids.view(-1, input_ids.size(-1)) if input_ids is not None else None
        attention_mask = attention_mask.view(-1, attention_mask.size(-1)) if attention_mask is not None else None
        position_ids = position_ids.view(-1, position_ids.size(-1)) if position_ids is not None else None
        inputs_embeds = (
            inputs_embeds.view(-1, inputs_embeds.size(-2), inputs_embeds.size(-1))
            if inputs_embeds is not None
            else None
        )

        outputs = self.model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            position_ids=position_ids,
            inputs_embeds=inputs_embeds,
            **kwargs,
        )
        last_hidden_state = outputs[0]  # shape (num_choices, seq_len, hidden_size)

        # If classifier_pooling is "cls", isolate the <cls> token
        if self.config.classifier_pooling == "cls":
            indices_0 = torch.arange(last_hidden_state.shape[0], device=last_hidden_state.device)
            # for left or right padding, <cls> is the first non-pad token
            if attention_mask is not None:
                cls_mask = attention_mask.argmax(dim=-1).to(last_hidden_state.device)
            # if no pad, <cls> is the first token
            else:
                cls_mask = torch.tensor(0, dtype=torch.long, device=last_hidden_state.device)
            # extract the <cls> token for the logits
            last_hidden_state = last_hidden_state[indices_0, cls_mask]

        # If classifier_pooling is "mean", pool the hidden states by averaging over the sequence length
        elif self.config.classifier_pooling == "mean":
            num_non_pad_tokens = attention_mask.sum(dim=1, keepdim=True)
            last_hidden_state = (last_hidden_state * attention_mask.unsqueeze(-1)).sum(dim=1) / num_non_pad_tokens

        pooled_output = self.head(last_hidden_state)
        pooled_output = self.drop(pooled_output)
        logits = self.classifier(pooled_output)

        reshaped_logits = logits.view(-1, num_choices)

        loss = None
        if labels is not None:
            loss_fct = nn.CrossEntropyLoss()
            loss = loss_fct(reshaped_logits, labels)

        return MultipleChoiceModelOutput(
            loss=loss,
            logits=reshaped_logits,
            hidden_states=outputs.hidden_states,
            attentions=outputs.attentions,
        )