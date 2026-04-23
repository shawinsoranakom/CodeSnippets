def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        attention_mask: torch.FloatTensor | None = None,
        question_lengths: torch.LongTensor | None = None,
        token_type_ids: torch.LongTensor | None = None,
        position_ids: torch.LongTensor | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        start_positions: torch.LongTensor | None = None,
        end_positions: torch.LongTensor | None = None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> BigBirdForQuestionAnsweringModelOutput:
        r"""
        question_lengths (`torch.LongTensor` of shape `(batch_size, 1)`, *optional*):
            The lengths of the questions in the batch.

        Example:

        ```python
        >>> import torch
        >>> from transformers import AutoTokenizer, BigBirdForQuestionAnswering
        >>> from datasets import load_dataset

        >>> tokenizer = AutoTokenizer.from_pretrained("google/bigbird-roberta-base")
        >>> model = BigBirdForQuestionAnswering.from_pretrained("google/bigbird-roberta-base")
        >>> squad_ds = load_dataset("rajpurkar/squad_v2", split="train")  # doctest: +IGNORE_RESULT

        >>> # select random article and question
        >>> LONG_ARTICLE = squad_ds[81514]["context"]
        >>> QUESTION = squad_ds[81514]["question"]
        >>> QUESTION
        'During daytime how high can the temperatures reach?'

        >>> inputs = tokenizer(QUESTION, LONG_ARTICLE, return_tensors="pt")
        >>> # long article and question input
        >>> list(inputs["input_ids"].shape)
        [1, 929]

        >>> with torch.no_grad():
        ...     outputs = model(**inputs)

        >>> answer_start_index = outputs.start_logits.argmax()
        >>> answer_end_index = outputs.end_logits.argmax()
        >>> predict_answer_token_ids = inputs.input_ids[0, answer_start_index : answer_end_index + 1]
        >>> predict_answer_token = tokenizer.decode(predict_answer_token_ids)
        ```

        ```python
        >>> target_start_index, target_end_index = torch.tensor([130]), torch.tensor([132])
        >>> outputs = model(**inputs, start_positions=target_start_index, end_positions=target_end_index)
        >>> loss = outputs.loss
        ```
        """
        seqlen = input_ids.size(1) if input_ids is not None else inputs_embeds.size(1)

        if question_lengths is None and input_ids is not None:
            # assuming input_ids format: <cls> <question> <sep> context <sep>
            question_lengths = torch.argmax(input_ids.eq(self.sep_token_id).int(), dim=-1) + 1
            question_lengths.unsqueeze_(1)

        logits_mask = None
        if question_lengths is not None:
            # setting lengths logits to `-inf`
            logits_mask = self.prepare_question_mask(question_lengths, seqlen)
            if token_type_ids is None:
                token_type_ids = torch.ones(logits_mask.size(), dtype=int, device=logits_mask.device) - logits_mask
            logits_mask[:, 0] = False
            logits_mask.unsqueeze_(2)

        outputs: BaseModelOutputWithPoolingAndCrossAttentions = self.bert(
            input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            position_ids=position_ids,
            inputs_embeds=inputs_embeds,
            **kwargs,
        )

        sequence_output = outputs.last_hidden_state
        logits = self.qa_classifier(sequence_output)

        if logits_mask is not None:
            # removing question tokens from the competition
            logits = logits - logits_mask * 1e6

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

        return BigBirdForQuestionAnsweringModelOutput(
            loss=total_loss,
            start_logits=start_logits,
            end_logits=end_logits,
            pooler_output=outputs.pooler_output,
            hidden_states=outputs.hidden_states,
            attentions=outputs.attentions,
        )