def _batch_encode_plus(
        self,
        batch_text_or_text_pairs: list[TextInput] | list[TextInputPair],
        batch_entity_spans_or_entity_spans_pairs: list[EntitySpanInput]
        | list[tuple[EntitySpanInput, EntitySpanInput]]
        | None = None,
        batch_entities_or_entities_pairs: list[EntityInput] | list[tuple[EntityInput, EntityInput]] | None = None,
        add_special_tokens: bool = True,
        padding_strategy: PaddingStrategy = PaddingStrategy.DO_NOT_PAD,
        truncation_strategy: TruncationStrategy = TruncationStrategy.DO_NOT_TRUNCATE,
        max_length: int | None = None,
        max_entity_length: int | None = None,
        stride: int = 0,
        is_split_into_words: bool | None = False,
        pad_to_multiple_of: int | None = None,
        padding_side: str | None = None,
        return_tensors: str | TensorType | None = None,
        return_token_type_ids: bool | None = None,
        return_attention_mask: bool | None = None,
        return_overflowing_tokens: bool = False,
        return_special_tokens_mask: bool = False,
        return_offsets_mapping: bool = False,
        return_length: bool = False,
        verbose: bool = True,
        **kwargs,
    ) -> BatchEncoding:
        if (
            batch_entity_spans_or_entity_spans_pairs is None
            and batch_entities_or_entities_pairs is None
            and self.task is None
        ):
            if batch_text_or_text_pairs and isinstance(batch_text_or_text_pairs[0], (tuple, list)):
                texts, text_pairs = zip(*batch_text_or_text_pairs)
                texts = list(texts)
                text_pairs = list(text_pairs)
            else:
                texts = batch_text_or_text_pairs
                text_pairs = None

            return super()._encode_plus(
                text=texts,
                text_pair=text_pairs,
                add_special_tokens=add_special_tokens,
                padding_strategy=padding_strategy,
                truncation_strategy=truncation_strategy,
                max_length=max_length,
                stride=stride,
                is_split_into_words=is_split_into_words,
                pad_to_multiple_of=pad_to_multiple_of,
                padding_side=padding_side,
                return_tensors=return_tensors,
                return_token_type_ids=return_token_type_ids,
                return_attention_mask=return_attention_mask,
                return_overflowing_tokens=return_overflowing_tokens,
                return_special_tokens_mask=return_special_tokens_mask,
                return_offsets_mapping=return_offsets_mapping,
                return_length=return_length,
                verbose=verbose,
                **kwargs,
            )

        if return_offsets_mapping:
            raise NotImplementedError(
                "return_offset_mapping is not available when using Python tokenizers. "
                "To use this feature, change your tokenizer to one deriving from "
                "transformers.PreTrainedTokenizerFast."
            )

        if is_split_into_words:
            raise NotImplementedError("is_split_into_words is not supported in this tokenizer.")

        # input_ids is a list of tuples (one for each example in the batch)
        input_ids = []
        entity_ids = []
        entity_token_spans = []
        for index, text_or_text_pair in enumerate(batch_text_or_text_pairs):
            if not isinstance(text_or_text_pair, (list, tuple)):
                text, text_pair = text_or_text_pair, None
            else:
                text, text_pair = text_or_text_pair

            entities, entities_pair = None, None
            if batch_entities_or_entities_pairs is not None:
                entities_or_entities_pairs = batch_entities_or_entities_pairs[index]
                if entities_or_entities_pairs:
                    if isinstance(entities_or_entities_pairs[0], str):
                        entities, entities_pair = entities_or_entities_pairs, None
                    else:
                        entities, entities_pair = entities_or_entities_pairs

            entity_spans, entity_spans_pair = None, None
            if batch_entity_spans_or_entity_spans_pairs is not None:
                entity_spans_or_entity_spans_pairs = batch_entity_spans_or_entity_spans_pairs[index]
                if len(entity_spans_or_entity_spans_pairs) > 0 and isinstance(
                    entity_spans_or_entity_spans_pairs[0], list
                ):
                    entity_spans, entity_spans_pair = entity_spans_or_entity_spans_pairs
                else:
                    entity_spans, entity_spans_pair = entity_spans_or_entity_spans_pairs, None

            (
                first_ids,
                second_ids,
                first_entity_ids,
                second_entity_ids,
                first_entity_token_spans,
                second_entity_token_spans,
            ) = self._create_input_sequence(
                text=text,
                text_pair=text_pair,
                entities=entities,
                entities_pair=entities_pair,
                entity_spans=entity_spans,
                entity_spans_pair=entity_spans_pair,
                **kwargs,
            )
            input_ids.append((first_ids, second_ids))
            entity_ids.append((first_entity_ids, second_entity_ids))
            entity_token_spans.append((first_entity_token_spans, second_entity_token_spans))

        batch_outputs = self._batch_prepare_for_model(
            input_ids,
            batch_entity_ids_pairs=entity_ids,
            batch_entity_token_spans_pairs=entity_token_spans,
            add_special_tokens=add_special_tokens,
            padding_strategy=padding_strategy,
            truncation_strategy=truncation_strategy,
            max_length=max_length,
            max_entity_length=max_entity_length,
            stride=stride,
            pad_to_multiple_of=pad_to_multiple_of,
            padding_side=padding_side,
            return_attention_mask=return_attention_mask,
            return_token_type_ids=return_token_type_ids,
            return_overflowing_tokens=return_overflowing_tokens,
            return_special_tokens_mask=return_special_tokens_mask,
            return_length=return_length,
            return_tensors=return_tensors,
            verbose=verbose,
        )

        return BatchEncoding(batch_outputs)