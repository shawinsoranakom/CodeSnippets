def __call__(
        self,
        text: TextInput | list[TextInput],
        text_pair: TextInput | list[TextInput] | None = None,
        entity_spans: EntitySpanInput | list[EntitySpanInput] | None = None,
        entity_spans_pair: EntitySpanInput | list[EntitySpanInput] | None = None,
        entities: EntityInput | list[EntityInput] | None = None,
        entities_pair: EntityInput | list[EntityInput] | None = None,
        add_special_tokens: bool = True,
        padding: bool | str | PaddingStrategy = False,
        truncation: bool | str | TruncationStrategy = None,
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
        # Check for seq2seq parameters that are not supported with entity-aware encoding
        if kwargs.get("text_target") is not None or kwargs.get("text_pair_target") is not None:
            if entity_spans is not None or entities is not None or self.task is not None:
                raise NotImplementedError(
                    "text_target and text_pair_target are not supported when using entity-aware encoding. "
                    "Please use the tokenizer without entities for seq2seq tasks."
                )
            # Delegate to parent for seq2seq encoding
            return super().__call__(
                text=text,
                text_pair=text_pair,
                add_special_tokens=add_special_tokens,
                padding=padding,
                truncation=truncation,
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
        """
        Main method to tokenize and prepare for the model one or several sequence(s) or one or several pair(s) of
        sequences, depending on the task you want to prepare them for.

        Args:
            text (`str`, `list[str]`, `list[list[str]]`):
                The sequence or batch of sequences to be encoded. Each sequence must be a string. Note that this
                tokenizer does not support tokenization based on pretokenized strings.
            text_pair (`str`, `list[str]`, `list[list[str]]`):
                The sequence or batch of sequences to be encoded. Each sequence must be a string. Note that this
                tokenizer does not support tokenization based on pretokenized strings.
            entity_spans (`list[tuple[int, int]]`, `list[list[tuple[int, int]]]`, *optional*):
                The sequence or batch of sequences of entity spans to be encoded. Each sequence consists of tuples each
                with two integers denoting character-based start and end positions of entities. If you specify
                `"entity_classification"` or `"entity_pair_classification"` as the `task` argument in the constructor,
                the length of each sequence must be 1 or 2, respectively. If you specify `entities`, the length of each
                sequence must be equal to the length of each sequence of `entities`.
            entity_spans_pair (`list[tuple[int, int]]`, `list[list[tuple[int, int]]]`, *optional*):
                The sequence or batch of sequences of entity spans to be encoded. Each sequence consists of tuples each
                with two integers denoting character-based start and end positions of entities. If you specify the
                `task` argument in the constructor, this argument is ignored. If you specify `entities_pair`, the
                length of each sequence must be equal to the length of each sequence of `entities_pair`.
            entities (`list[str]`, `list[list[str]]`, *optional*):
                The sequence or batch of sequences of entities to be encoded. Each sequence consists of strings
                representing entities, i.e., special entities (e.g., [MASK]) or entity titles of Wikipedia (e.g., Los
                Angeles). This argument is ignored if you specify the `task` argument in the constructor. The length of
                each sequence must be equal to the length of each sequence of `entity_spans`. If you specify
                `entity_spans` without specifying this argument, the entity sequence or the batch of entity sequences
                is automatically constructed by filling it with the [MASK] entity.
            entities_pair (`list[str]`, `list[list[str]]`, *optional*):
                The sequence or batch of sequences of entities to be encoded. Each sequence consists of strings
                representing entities, i.e., special entities (e.g., [MASK]) or entity titles of Wikipedia (e.g., Los
                Angeles). This argument is ignored if you specify the `task` argument in the constructor. The length of
                each sequence must be equal to the length of each sequence of `entity_spans_pair`. If you specify
                `entity_spans_pair` without specifying this argument, the entity sequence or the batch of entity
                sequences is automatically constructed by filling it with the [MASK] entity.
            max_entity_length (`int`, *optional*):
                The maximum length of `entity_ids`.
        """
        # Input type checking for clearer error
        is_valid_single_text = isinstance(text, str)
        is_valid_batch_text = isinstance(text, (list, tuple)) and (
            len(text) == 0 or isinstance(text[0], (str, list, tuple))
        )
        if not (is_valid_single_text or is_valid_batch_text):
            raise ValueError(
                "text input must be of type `str` (single example), `list[str]` (batch), or `list[tuple]` (batch pairs)."
            )

        is_valid_single_text_pair = isinstance(text_pair, str)
        is_valid_batch_text_pair = isinstance(text_pair, (list, tuple)) and (
            len(text_pair) == 0 or isinstance(text_pair[0], str)
        )
        if not (text_pair is None or is_valid_single_text_pair or is_valid_batch_text_pair):
            raise ValueError("text_pair input must be of type `str` (single example) or `list[str]` (batch).")

        is_batched = bool(isinstance(text, (list, tuple)))

        # Convert padding and truncation to strategies
        padding_strategy, truncation_strategy, max_length, kwargs = self._get_padding_truncation_strategies(
            padding=padding,
            truncation=truncation,
            max_length=max_length,
            pad_to_multiple_of=pad_to_multiple_of,
            verbose=verbose,
            **kwargs,
        )

        if is_batched:
            batch_text_or_text_pairs = list(zip(text, text_pair)) if text_pair is not None else text
            if entities is None:
                batch_entities_or_entities_pairs = None
            else:
                batch_entities_or_entities_pairs = (
                    list(zip(entities, entities_pair)) if entities_pair is not None else entities
                )

            if entity_spans is None:
                batch_entity_spans_or_entity_spans_pairs = None
            else:
                batch_entity_spans_or_entity_spans_pairs = (
                    list(zip(entity_spans, entity_spans_pair)) if entity_spans_pair is not None else entity_spans
                )

            return self._batch_encode_plus(
                batch_text_or_text_pairs=batch_text_or_text_pairs,
                batch_entity_spans_or_entity_spans_pairs=batch_entity_spans_or_entity_spans_pairs,
                batch_entities_or_entities_pairs=batch_entities_or_entities_pairs,
                add_special_tokens=add_special_tokens,
                padding_strategy=padding_strategy,
                truncation_strategy=truncation_strategy,
                max_length=max_length,
                max_entity_length=max_entity_length,
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
        else:
            return self._encode_plus(
                text=text,
                text_pair=text_pair,
                entity_spans=entity_spans,
                entity_spans_pair=entity_spans_pair,
                entities=entities,
                entities_pair=entities_pair,
                add_special_tokens=add_special_tokens,
                padding_strategy=padding_strategy,
                truncation_strategy=truncation_strategy,
                max_length=max_length,
                max_entity_length=max_entity_length,
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