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
    ) -> tuple | SplinterForPreTrainingOutput:
        r"""
        input_ids (`torch.LongTensor` of shape `(batch_size, num_questions, sequence_length)`):
            Indices of input sequence tokens in the vocabulary.

            Indices can be obtained using [`AutoTokenizer`]. See [`PreTrainedTokenizer.encode`] and
            [`PreTrainedTokenizer.__call__`] for details.

            [What are input IDs?](../glossary#input-ids)
        token_type_ids (`torch.LongTensor` of shape `batch_size, num_questions, sequence_length`, *optional*):
            Segment token indices to indicate first and second portions of the inputs. Indices are selected in `[0,
            1]`:

            - 0 corresponds to a *sentence A* token,
            - 1 corresponds to a *sentence B* token.

            [What are token type IDs?](../glossary#token-type-ids)
        position_ids (`torch.LongTensor` of shape `batch_size, num_questions, sequence_length`, *optional*):
            Indices of positions of each input sequence tokens in the position embeddings. Selected in the range `[0,
            config.max_position_embeddings - 1]`.

            [What are position IDs?](../glossary#position-ids)
        inputs_embeds (`torch.FloatTensor` of shape `(batch_size, num_questions, sequence_length, hidden_size)`, *optional*):
            Optionally, instead of passing `input_ids` you can choose to directly pass an embedded representation. This
            is useful if you want more control over how to convert *input_ids* indices into associated vectors than the
            model's internal embedding lookup matrix.
        start_positions (`torch.LongTensor` of shape `(batch_size, num_questions)`, *optional*):
            Labels for position (index) of the start of the labelled span for computing the token classification loss.
            Positions are clamped to the length of the sequence (`sequence_length`). Position outside of the sequence
            are not taken into account for computing the loss.
        end_positions (`torch.LongTensor` of shape `(batch_size, num_questions)`, *optional*):
            Labels for position (index) of the end of the labelled span for computing the token classification loss.
            Positions are clamped to the length of the sequence (`sequence_length`). Position outside of the sequence
            are not taken into account for computing the loss.
        question_positions (`torch.LongTensor` of shape `(batch_size, num_questions)`, *optional*):
            The positions of all question tokens. If given, start_logits and end_logits will be of shape `(batch_size,
            num_questions, sequence_length)`. If None, the first question token in each sequence in the batch will be
            the only one for which start_logits and end_logits are calculated and they will be of shape `(batch_size,
            sequence_length)`.
        """
        if question_positions is None and start_positions is not None and end_positions is not None:
            raise TypeError("question_positions must be specified in order to calculate the loss")

        elif question_positions is None and input_ids is None:
            raise TypeError("question_positions must be specified when inputs_embeds is used")

        elif question_positions is None:
            question_positions = self._prepare_question_positions(input_ids)

        outputs = self.splinter(
            input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            position_ids=position_ids,
            inputs_embeds=inputs_embeds,
            **kwargs,
        )

        sequence_output = outputs[0]
        batch_size, sequence_length, dim = sequence_output.size()
        # [batch_size, num_questions, sequence_length]
        start_logits, end_logits = self.splinter_qass(sequence_output, question_positions)

        num_questions = question_positions.size(1)
        if attention_mask is not None:
            attention_mask_for_each_question = attention_mask.unsqueeze(1).expand(
                batch_size, num_questions, sequence_length
            )
            start_logits = start_logits + (1 - attention_mask_for_each_question) * torch.finfo(start_logits.dtype).min
            end_logits = end_logits + (1 - attention_mask_for_each_question) * torch.finfo(end_logits.dtype).min

        total_loss = None
        # [batch_size, num_questions, sequence_length]
        if start_positions is not None and end_positions is not None:
            # sometimes the start/end positions are outside our model inputs, we ignore these terms
            start_positions.clamp_(0, max(0, sequence_length - 1))
            end_positions.clamp_(0, max(0, sequence_length - 1))

            # Ignore zero positions in the loss. Splinter never predicts zero
            # during pretraining and zero is used for padding question
            # tokens as well as for start and end positions of padded
            # question tokens.
            loss_fct = CrossEntropyLoss(ignore_index=self.config.pad_token_id)
            start_loss = loss_fct(
                start_logits.view(batch_size * num_questions, sequence_length),
                start_positions.view(batch_size * num_questions),
            )
            end_loss = loss_fct(
                end_logits.view(batch_size * num_questions, sequence_length),
                end_positions.view(batch_size * num_questions),
            )
            total_loss = (start_loss + end_loss) / 2

        return SplinterForPreTrainingOutput(
            loss=total_loss,
            start_logits=start_logits,
            end_logits=end_logits,
            hidden_states=outputs.hidden_states,
            attentions=outputs.attentions,
        )