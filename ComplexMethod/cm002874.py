def forward(
        self,
        input_ids: torch.Tensor | None = None,
        attention_mask: torch.Tensor | None = None,
        global_attention_mask: torch.Tensor | None = None,
        token_type_ids: torch.Tensor | None = None,
        position_ids: torch.Tensor | None = None,
        inputs_embeds: torch.Tensor | None = None,
        start_positions: torch.Tensor | None = None,
        end_positions: torch.Tensor | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple | LongformerQuestionAnsweringModelOutput:
        r"""
        global_attention_mask (`torch.FloatTensor` of shape `(batch_size, sequence_length)`, *optional*):
            Mask to decide the attention given on each token, local attention or global attention. Tokens with global
            attention attends to all other tokens, and all other tokens attend to them. This is important for
            task-specific finetuning because it makes the model more flexible at representing the task. For example,
            for classification, the <s> token should be given global attention. For QA, all question tokens should also
            have global attention. Please refer to the [Longformer paper](https://huggingface.co/papers/2004.05150) for more
            details. Mask values selected in `[0, 1]`:

            - 0 for local attention (a sliding window attention),
            - 1 for global attention (tokens that attend to all other tokens, and all other tokens attend to them).

        Examples:

        ```python
        >>> from transformers import AutoTokenizer, LongformerForQuestionAnswering
        >>> import torch

        >>> tokenizer = AutoTokenizer.from_pretrained("allenai/longformer-large-4096-finetuned-triviaqa")
        >>> model = LongformerForQuestionAnswering.from_pretrained("allenai/longformer-large-4096-finetuned-triviaqa")

        >>> question, text = "Who was Jim Henson?", "Jim Henson was a nice puppet"
        >>> encoding = tokenizer(question, text, return_tensors="pt")
        >>> input_ids = encoding["input_ids"]

        >>> # default is local attention everywhere
        >>> # the forward method will automatically set global attention on question tokens
        >>> attention_mask = encoding["attention_mask"]

        >>> outputs = model(input_ids, attention_mask=attention_mask)
        >>> start_logits = outputs.start_logits
        >>> end_logits = outputs.end_logits
        >>> all_tokens = tokenizer.convert_ids_to_tokens(input_ids[0].tolist())

        >>> answer_tokens = all_tokens[torch.argmax(start_logits) : torch.argmax(end_logits) + 1]
        >>> answer = tokenizer.decode(
        ...     tokenizer.convert_tokens_to_ids(answer_tokens)
        ... )  # remove space prepending space token
        ```"""
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        if global_attention_mask is None:
            if input_ids is None:
                logger.warning(
                    "It is not possible to automatically generate the `global_attention_mask` because input_ids is"
                    " None. Please make sure that it is correctly set."
                )
            else:
                # set global attention on question tokens automatically
                global_attention_mask = _compute_global_attention_mask(input_ids, self.config.sep_token_id)

        outputs = self.longformer(
            input_ids,
            attention_mask=attention_mask,
            global_attention_mask=global_attention_mask,
            token_type_ids=token_type_ids,
            position_ids=position_ids,
            inputs_embeds=inputs_embeds,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )

        sequence_output = outputs[0]

        logits = self.qa_outputs(sequence_output)
        start_logits, end_logits = logits.split(1, dim=-1)
        start_logits = start_logits.squeeze(-1).contiguous()
        end_logits = end_logits.squeeze(-1).contiguous()

        total_loss = None
        if start_positions is not None and end_positions is not None:
            # If we are on multi-GPU, split add a dimension
            if len(start_positions.size()) > 1:
                start_positions = start_positions.squeeze(-1)
            if len(end_positions.size()) > 1:
                end_positions = end_positions.squeeze(-1)
            # sometimes the start/end positions are outside our model inputs, we ignore these terms
            ignored_index = start_logits.size(1)
            start_positions = start_positions.clamp(0, ignored_index)
            end_positions = end_positions.clamp(0, ignored_index)

            loss_fct = CrossEntropyLoss(ignore_index=ignored_index)
            start_loss = loss_fct(start_logits, start_positions)
            end_loss = loss_fct(end_logits, end_positions)
            total_loss = (start_loss + end_loss) / 2

        if not return_dict:
            output = (start_logits, end_logits) + outputs[2:]
            return ((total_loss,) + output) if total_loss is not None else output

        return LongformerQuestionAnsweringModelOutput(
            loss=total_loss,
            start_logits=start_logits,
            end_logits=end_logits,
            hidden_states=outputs.hidden_states,
            attentions=outputs.attentions,
            global_attentions=outputs.global_attentions,
        )