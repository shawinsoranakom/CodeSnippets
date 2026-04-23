def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        attention_mask: torch.FloatTensor | None = None,
        token_type_ids: torch.LongTensor | None = None,
        position_ids: torch.LongTensor | None = None,
        entity_ids: torch.LongTensor | None = None,
        entity_attention_mask: torch.LongTensor | None = None,
        entity_token_type_ids: torch.LongTensor | None = None,
        entity_position_ids: torch.LongTensor | None = None,
        labels: torch.LongTensor | None = None,
        entity_labels: torch.LongTensor | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple | LukeMaskedLMOutput:
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
        labels (`torch.LongTensor` of shape `(batch_size, sequence_length)`, *optional*):
            Labels for computing the masked language modeling loss. Indices should be in `[-100, 0, ...,
            config.vocab_size]` (see `input_ids` docstring) Tokens with indices set to `-100` are ignored (masked), the
            loss is only computed for the tokens with labels in `[0, ..., config.vocab_size]`
        entity_labels (`torch.LongTensor` of shape `(batch_size, entity_length)`, *optional*):
            Labels for computing the masked language modeling loss. Indices should be in `[-100, 0, ...,
            config.vocab_size]` (see `input_ids` docstring) Tokens with indices set to `-100` are ignored (masked), the
            loss is only computed for the tokens with labels in `[0, ..., config.vocab_size]`
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

        loss = None

        mlm_loss = None
        logits = self.lm_head(outputs.last_hidden_state)
        if labels is not None:
            # move labels to correct device
            labels = labels.to(logits.device)
            mlm_loss = self.loss_fn(logits.view(-1, self.config.vocab_size), labels.view(-1))
            if loss is None:
                loss = mlm_loss

        mep_loss = None
        entity_logits = None
        if outputs.entity_last_hidden_state is not None:
            entity_logits = self.entity_predictions(outputs.entity_last_hidden_state)
            if entity_labels is not None:
                mep_loss = self.loss_fn(entity_logits.view(-1, self.config.entity_vocab_size), entity_labels.view(-1))
                if loss is None:
                    loss = mep_loss
                else:
                    loss = loss + mep_loss

        if not return_dict:
            return tuple(
                v
                for v in [
                    loss,
                    mlm_loss,
                    mep_loss,
                    logits,
                    entity_logits,
                    outputs.hidden_states,
                    outputs.entity_hidden_states,
                    outputs.attentions,
                ]
                if v is not None
            )

        return LukeMaskedLMOutput(
            loss=loss,
            mlm_loss=mlm_loss,
            mep_loss=mep_loss,
            logits=logits,
            entity_logits=entity_logits,
            hidden_states=outputs.hidden_states,
            entity_hidden_states=outputs.entity_hidden_states,
            attentions=outputs.attentions,
        )