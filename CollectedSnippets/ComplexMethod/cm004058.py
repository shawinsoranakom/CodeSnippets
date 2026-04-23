def forward(
        self,
        input_ids: torch.Tensor | None = None,
        attention_mask: torch.Tensor | None = None,
        token_type_ids: torch.Tensor | None = None,
        position_ids: torch.Tensor | None = None,
        inputs_embeds: torch.Tensor | None = None,
        start_positions: torch.LongTensor | None = None,
        end_positions: torch.LongTensor | None = None,
        question_positions: torch.LongTensor | None = None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> tuple | QuestionAnsweringModelOutput:
        r"""
        token_type_ids (`torch.LongTensor` of shape `batch_size, sequence_length`, *optional*):
            Segment token indices to indicate first and second portions of the inputs. Indices are selected in `[0,
            1]`:

            - 0 corresponds to a *sentence A* token,
            - 1 corresponds to a *sentence B* token.

            [What are token type IDs?](../glossary#token-type-ids)
        position_ids (`torch.LongTensor` of shape `batch_size, sequence_length`, *optional*):
            Indices of positions of each input sequence tokens in the position embeddings. Selected in the range `[0,
            config.max_position_embeddings - 1]`.

            [What are position IDs?](../glossary#position-ids)
        question_positions (`torch.LongTensor` of shape `(batch_size, num_questions)`, *optional*):
            The positions of all question tokens. If given, start_logits and end_logits will be of shape `(batch_size,
            num_questions, sequence_length)`. If None, the first question token in each sequence in the batch will be
            the only one for which start_logits and end_logits are calculated and they will be of shape `(batch_size,
            sequence_length)`.
        """
        question_positions_were_none = False
        if question_positions is None:
            if input_ids is not None:
                question_position_for_each_example = torch.argmax(
                    (torch.eq(input_ids, self.question_token_id)).int(), dim=-1
                )
            else:
                question_position_for_each_example = torch.zeros(
                    inputs_embeds.size(0), dtype=torch.long, layout=inputs_embeds.layout, device=inputs_embeds.device
                )
            question_positions = question_position_for_each_example.unsqueeze(-1)
            question_positions_were_none = True

        outputs = self.splinter(
            input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            position_ids=position_ids,
            inputs_embeds=inputs_embeds,
            **kwargs,
        )

        sequence_output = outputs[0]
        start_logits, end_logits = self.splinter_qass(sequence_output, question_positions)

        if question_positions_were_none:
            start_logits, end_logits = start_logits.squeeze(1), end_logits.squeeze(1)

        if attention_mask is not None:
            start_logits = start_logits + (1 - attention_mask) * torch.finfo(start_logits.dtype).min
            end_logits = end_logits + (1 - attention_mask) * torch.finfo(end_logits.dtype).min

        total_loss = None
        if start_positions is not None and end_positions is not None:
            # If we are on multi-GPU, split add a dimension
            if len(start_positions.size()) > 1:
                start_positions = start_positions.squeeze(-1)
            if len(end_positions.size()) > 1:
                end_positions = end_positions.squeeze(-1)
            # sometimes the start/end positions are outside our model inputs, we ignore these terms
            ignored_index = start_logits.size(1)
            start_positions.clamp_(0, ignored_index)
            end_positions.clamp_(0, ignored_index)

            loss_fct = CrossEntropyLoss(ignore_index=ignored_index)
            start_loss = loss_fct(start_logits, start_positions)
            end_loss = loss_fct(end_logits, end_positions)
            total_loss = (start_loss + end_loss) / 2

        return QuestionAnsweringModelOutput(
            loss=total_loss,
            start_logits=start_logits,
            end_logits=end_logits,
            hidden_states=outputs.hidden_states,
            attentions=outputs.attentions,
        )