def forward(
        self,
        input_ids: torch.Tensor | None = None,
        token_type_ids: torch.Tensor | None = None,
        attention_mask: torch.Tensor | None = None,
        global_attention_mask: torch.Tensor | None = None,
        labels: torch.Tensor | None = None,
        position_ids: torch.Tensor | None = None,
        inputs_embeds: torch.Tensor | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple | LongformerMultipleChoiceModelOutput:
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
        global_attention_mask (`torch.FloatTensor` of shape `(batch_size, num_choices, sequence_length)`, *optional*):
            Mask to decide the attention given on each token, local attention or global attention. Tokens with global
            attention attends to all other tokens, and all other tokens attend to them. This is important for
            task-specific finetuning because it makes the model more flexible at representing the task. For example,
            for classification, the <s> token should be given global attention. For QA, all question tokens should also
            have global attention. Please refer to the [Longformer paper](https://huggingface.co/papers/2004.05150) for more
            details. Mask values selected in `[0, 1]`:

            - 0 for local attention (a sliding window attention),
            - 1 for global attention (tokens that attend to all other tokens, and all other tokens attend to them).
        labels (`torch.LongTensor` of shape `(batch_size,)`, *optional*):
            Labels for computing the multiple choice classification loss. Indices should be in `[0, ...,
            num_choices-1]` where `num_choices` is the size of the second dimension of the input tensors. (See
            `input_ids` above)
        position_ids (`torch.LongTensor` of shape `(batch_size, num_choices, sequence_length)`, *optional*):
            Indices of positions of each input sequence tokens in the position embeddings. Selected in the range `[0,
            config.max_position_embeddings - 1]`.

            [What are position IDs?](../glossary#position-ids)
        inputs_embeds (`torch.FloatTensor` of shape `(batch_size, num_choices, sequence_length, hidden_size)`, *optional*):
            Optionally, instead of passing `input_ids` you can choose to directly pass an embedded representation. This
            is useful if you want more control over how to convert `input_ids` indices into associated vectors than the
            model's internal embedding lookup matrix.
        """
        num_choices = input_ids.shape[1] if input_ids is not None else inputs_embeds.shape[1]
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        # set global attention on question tokens
        if global_attention_mask is None and input_ids is not None:
            logger.warning_once("Initializing global attention on multiple choice...")
            # put global attention on all tokens after `config.sep_token_id`
            global_attention_mask = torch.stack(
                [
                    _compute_global_attention_mask(input_ids[:, i], self.config.sep_token_id, before_sep_token=False)
                    for i in range(num_choices)
                ],
                dim=1,
            )

        flat_input_ids = input_ids.view(-1, input_ids.size(-1)) if input_ids is not None else None
        flat_position_ids = position_ids.view(-1, position_ids.size(-1)) if position_ids is not None else None
        flat_token_type_ids = token_type_ids.view(-1, token_type_ids.size(-1)) if token_type_ids is not None else None
        flat_attention_mask = attention_mask.view(-1, attention_mask.size(-1)) if attention_mask is not None else None
        flat_global_attention_mask = (
            global_attention_mask.view(-1, global_attention_mask.size(-1))
            if global_attention_mask is not None
            else None
        )
        flat_inputs_embeds = (
            inputs_embeds.view(-1, inputs_embeds.size(-2), inputs_embeds.size(-1))
            if inputs_embeds is not None
            else None
        )

        outputs = self.longformer(
            flat_input_ids,
            position_ids=flat_position_ids,
            token_type_ids=flat_token_type_ids,
            attention_mask=flat_attention_mask,
            global_attention_mask=flat_global_attention_mask,
            inputs_embeds=flat_inputs_embeds,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )
        pooled_output = outputs[1]

        pooled_output = self.dropout(pooled_output)
        logits = self.classifier(pooled_output)
        reshaped_logits = logits.view(-1, num_choices)

        loss = None
        if labels is not None:
            loss_fct = CrossEntropyLoss()

            labels = labels.to(reshaped_logits.device)
            loss = loss_fct(reshaped_logits, labels)

        if not return_dict:
            output = (reshaped_logits,) + outputs[2:]
            return ((loss,) + output) if loss is not None else output

        return LongformerMultipleChoiceModelOutput(
            loss=loss,
            logits=reshaped_logits,
            hidden_states=outputs.hidden_states,
            attentions=outputs.attentions,
            global_attentions=outputs.global_attentions,
        )