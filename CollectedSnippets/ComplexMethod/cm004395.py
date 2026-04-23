def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        attention_mask: torch.FloatTensor | None = None,
        token_type_ids: torch.LongTensor | None = None,
        position_ids: torch.FloatTensor | None = None,
        entity_ids: torch.LongTensor | None = None,
        entity_attention_mask: torch.FloatTensor | None = None,
        entity_token_type_ids: torch.LongTensor | None = None,
        entity_position_ids: torch.LongTensor | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        start_positions: torch.LongTensor | None = None,
        end_positions: torch.LongTensor | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple | LukeQuestionAnsweringModelOutput:
        r"""
        entity_ids (`torch.LongTensor` of shape `(batch_size, entity_length)`):
            Indices of entity tokens in the entity vocabulary.

            Indices can be obtained using [`AutoTokenizer`]. See [`PreTrainedTokenizer.encode`] and
            [`PreTrainedTokenizer.__call__`] for details.
        entity_attention_mask (`torch.FloatTensor` of shape `(batch_size, entity_length)`, *optional*):
            Mask to avoid performing attention on padding entity token indices. Mask values selected in `[0, 1]`:

            - 1 for entity tokens that are **not masked**,
            - 0 for entity tokens that are **masked**.
        entity_token_type_ids (`torch.LongTensor` of shape `(batch_size, entity_length)`, *optional*):
            Segment token indices to indicate first and second portions of the entity token inputs. Indices are
            selected in `[0, 1]`:

            - 0 corresponds to a *portion A* entity token,
            - 1 corresponds to a *portion B* entity token.
        entity_position_ids (`torch.LongTensor` of shape `(batch_size, entity_length, max_mention_length)`, *optional*):
            Indices of positions of each input entity in the position embeddings. Selected in the range `[0,
            config.max_position_embeddings - 1]`.
        """
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        outputs = self.luke(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            position_ids=position_ids,
            entity_ids=entity_ids,
            entity_attention_mask=entity_attention_mask,
            entity_token_type_ids=entity_token_type_ids,
            entity_position_ids=entity_position_ids,
            inputs_embeds=inputs_embeds,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=True,
        )

        sequence_output = outputs.last_hidden_state

        logits = self.qa_outputs(sequence_output)
        start_logits, end_logits = logits.split(1, dim=-1)
        start_logits = start_logits.squeeze(-1)
        end_logits = end_logits.squeeze(-1)

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

        if not return_dict:
            return tuple(
                v
                for v in [
                    total_loss,
                    start_logits,
                    end_logits,
                    outputs.hidden_states,
                    outputs.entity_hidden_states,
                    outputs.attentions,
                ]
                if v is not None
            )

        return LukeQuestionAnsweringModelOutput(
            loss=total_loss,
            start_logits=start_logits,
            end_logits=end_logits,
            hidden_states=outputs.hidden_states,
            entity_hidden_states=outputs.entity_hidden_states,
            attentions=outputs.attentions,
        )