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
        entity_start_positions: torch.LongTensor | None = None,
        entity_end_positions: torch.LongTensor | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        labels: torch.LongTensor | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple | EntitySpanClassificationOutput:
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
        entity_start_positions (`torch.LongTensor`):
            The start positions of entities in the word token sequence.
        entity_end_positions (`torch.LongTensor`):
            The end positions of entities in the word token sequence.
        labels (`torch.LongTensor` of shape `(batch_size, entity_length)` or `(batch_size, entity_length, num_labels)`, *optional*):
            Labels for computing the classification loss. If the shape is `(batch_size, entity_length)`, the cross
            entropy loss is used for the single-label classification. In this case, labels should contain the indices
            that should be in `[0, ..., config.num_labels - 1]`. If the shape is `(batch_size, entity_length,
            num_labels)`, the binary cross entropy loss is used for the multi-label classification. In this case,
            labels should only contain `[0, 1]`, where 0 and 1 indicate false and true, respectively.

        Examples:

        ```python
        >>> from transformers import AutoTokenizer, LukeForEntitySpanClassification

        >>> tokenizer = AutoTokenizer.from_pretrained("studio-ousia/luke-large-finetuned-conll-2003")
        >>> model = LukeForEntitySpanClassification.from_pretrained("studio-ousia/luke-large-finetuned-conll-2003")

        >>> text = "Beyoncé lives in Los Angeles"
        # List all possible entity spans in the text

        >>> word_start_positions = [0, 8, 14, 17, 21]  # character-based start positions of word tokens
        >>> word_end_positions = [7, 13, 16, 20, 28]  # character-based end positions of word tokens
        >>> entity_spans = []
        >>> for i, start_pos in enumerate(word_start_positions):
        ...     for end_pos in word_end_positions[i:]:
        ...         entity_spans.append((start_pos, end_pos))

        >>> inputs = tokenizer(text, entity_spans=entity_spans, return_tensors="pt")
        >>> outputs = model(**inputs)
        >>> logits = outputs.logits
        >>> predicted_class_indices = logits.argmax(-1).squeeze().tolist()
        >>> for span, predicted_class_idx in zip(entity_spans, predicted_class_indices):
        ...     if predicted_class_idx != 0:
        ...         print(text[span[0] : span[1]], model.config.id2label[predicted_class_idx])
        Beyoncé PER
        Los Angeles LOC
        ```"""
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
        hidden_size = outputs.last_hidden_state.size(-1)

        entity_start_positions = entity_start_positions.unsqueeze(-1).expand(-1, -1, hidden_size)
        if entity_start_positions.device != outputs.last_hidden_state.device:
            entity_start_positions = entity_start_positions.to(outputs.last_hidden_state.device)
        start_states = torch.gather(outputs.last_hidden_state, -2, entity_start_positions)

        entity_end_positions = entity_end_positions.unsqueeze(-1).expand(-1, -1, hidden_size)
        if entity_end_positions.device != outputs.last_hidden_state.device:
            entity_end_positions = entity_end_positions.to(outputs.last_hidden_state.device)
        end_states = torch.gather(outputs.last_hidden_state, -2, entity_end_positions)

        feature_vector = torch.cat([start_states, end_states, outputs.entity_last_hidden_state], dim=2)

        feature_vector = self.dropout(feature_vector)
        logits = self.classifier(feature_vector)

        loss = None
        if labels is not None:
            # move labels to correct device
            labels = labels.to(logits.device)
            # When the number of dimension of `labels` is 2, cross entropy is used as the loss function. The binary
            # cross entropy is used otherwise.
            if labels.ndim == 2:
                loss = nn.functional.cross_entropy(logits.view(-1, self.num_labels), labels.view(-1))
            else:
                loss = nn.functional.binary_cross_entropy_with_logits(logits.view(-1), labels.view(-1).type_as(logits))

        if not return_dict:
            return tuple(
                v
                for v in [loss, logits, outputs.hidden_states, outputs.entity_hidden_states, outputs.attentions]
                if v is not None
            )

        return EntitySpanClassificationOutput(
            loss=loss,
            logits=logits,
            hidden_states=outputs.hidden_states,
            entity_hidden_states=outputs.entity_hidden_states,
            attentions=outputs.attentions,
        )