def _encode_plus(
        self,
        text: TextInput,
        text_pair: TextInput | None = None,
        entity_spans: EntitySpanInput | None = None,
        entity_spans_pair: EntitySpanInput | None = None,
        entities: EntityInput | None = None,
        entities_pair: EntityInput | None = None,
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
        # If no entities are provided and task doesn't require them, delegate to parent for proper Encoding support
        if (
            entity_spans is None
            and entity_spans_pair is None
            and entities is None
            and entities_pair is None
            and self.task is None
        ):
            # Delegate to parent TokenizersBackend which properly handles Encoding objects
            return super()._encode_plus(
                text=text,
                text_pair=text_pair,
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
            raise NotImplementedError("return_offset_mapping is not available when using entity-aware encoding.")

        if is_split_into_words:
            raise NotImplementedError("is_split_into_words is not supported in this tokenizer.")

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

        # prepare_for_model will create the attention_mask and token_type_ids
        return self.prepare_for_model(
            first_ids,
            pair_ids=second_ids,
            entity_ids=first_entity_ids,
            pair_entity_ids=second_entity_ids,
            entity_token_spans=first_entity_token_spans,
            pair_entity_token_spans=second_entity_token_spans,
            add_special_tokens=add_special_tokens,
            padding=padding_strategy.value,
            truncation=truncation_strategy.value,
            max_length=max_length,
            max_entity_length=max_entity_length,
            stride=stride,
            pad_to_multiple_of=pad_to_multiple_of,
            padding_side=padding_side,
            return_tensors=return_tensors,
            prepend_batch_axis=True,
            return_attention_mask=return_attention_mask,
            return_token_type_ids=return_token_type_ids,
            return_overflowing_tokens=return_overflowing_tokens,
            return_special_tokens_mask=return_special_tokens_mask,
            return_length=return_length,
            verbose=verbose,
        )