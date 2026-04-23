def _encode_plus(
        self,
        text: TextInput | PreTokenizedInput | list[TextInput] | list[PreTokenizedInput],
        text_pair: TextInput | PreTokenizedInput | list[TextInput] | list[PreTokenizedInput] | None = None,
        add_special_tokens: bool = True,
        padding_strategy: PaddingStrategy = PaddingStrategy.DO_NOT_PAD,
        truncation_strategy: TruncationStrategy = TruncationStrategy.DO_NOT_TRUNCATE,
        max_length: int | None = None,
        stride: int = 0,
        is_split_into_words: bool = False,
        pad_to_multiple_of: int | None = None,
        padding_side: str | None = None,
        return_tensors: bool | None = None,
        return_token_type_ids: bool | None = None,
        return_attention_mask: bool | None = None,
        return_overflowing_tokens: bool = False,
        return_special_tokens_mask: bool = False,
        return_offsets_mapping: bool = False,
        return_length: bool = False,
        verbose: bool = True,
        split_special_tokens: bool | None = None,
        **kwargs,
    ) -> BatchEncoding:
        # Input validation (from _call_one)
        def _is_valid_text_input(t):
            if isinstance(t, str):
                return True
            elif isinstance(t, (list, tuple)):
                if len(t) == 0:
                    return True
                elif isinstance(t[0], str):
                    return True
                elif isinstance(t[0], (list, tuple)):
                    if len(t[0]) == 0 or isinstance(t[0][0], str):
                        return True
                    elif isinstance(t[0][0], (list, tuple)):
                        return len(t[0][0]) == 0 or isinstance(t[0][0][0], str)
                    else:
                        return False
                else:
                    return False
            else:
                return False

        if not _is_valid_text_input(text):
            raise ValueError(
                "text input must be of type `str` (single example), `list[str]` (batch or single pretokenized example) "
                "or `list[list[str]]` (batch of pretokenized examples) or `list[tuple[list[str], list[str]]]` (batch of pretokenized sequence pairs)."
            )

        if text_pair is not None and not _is_valid_text_input(text_pair):
            raise ValueError(
                "text input must be of type `str` (single example), `list[str]` (batch or single pretokenized example) "
                "or `list[list[str]]` (batch of pretokenized examples) or `list[tuple[list[str], list[str]]]` (batch of pretokenized sequence pairs)."
            )

        # Batch detection (from _call_one)
        if is_split_into_words:
            is_batched = isinstance(text, (list, tuple)) and text and isinstance(text[0], (list, tuple))
        else:
            is_batched = isinstance(text, (list, tuple))

        if is_batched:
            # Batch validation
            if isinstance(text_pair, str):
                raise TypeError(
                    "when tokenizing batches of text, `text_pair` must be a list or tuple with the same length as"
                    " `text`."
                )
            if text_pair is not None and len(text) != len(text_pair):
                raise ValueError(
                    f"batch length of `text`: {len(text)} does not match batch length of `text_pair`:"
                    f" {len(text_pair)}."
                )
            batch_text_or_text_pairs = list(zip(text, text_pair)) if text_pair is not None else text
        else:
            # Single input - convert to batch format
            batch_text_or_text_pairs = [(text, text_pair)] if text_pair else [text]

        # Set tokenizer configuration (from _batch_encode_plus)
        if not isinstance(batch_text_or_text_pairs, (tuple, list)):
            raise TypeError(
                f"batch_text_or_text_pairs has to be a list or a tuple (got {type(batch_text_or_text_pairs)})"
            )

        self.set_truncation_and_padding(
            padding_strategy=padding_strategy,
            truncation_strategy=truncation_strategy,
            max_length=max_length,
            stride=stride,
            pad_to_multiple_of=pad_to_multiple_of,
            padding_side=padding_side,
        )

        # Use self.split_special_tokens as default if not explicitly provided
        if split_special_tokens is None:
            split_special_tokens = self.split_special_tokens

        if self._tokenizer.encode_special_tokens != split_special_tokens:
            self._tokenizer.encode_special_tokens = split_special_tokens

        # Direct rust backend call
        encodings = self._tokenizer.encode_batch(
            batch_text_or_text_pairs,
            add_special_tokens=add_special_tokens,
            is_pretokenized=is_split_into_words,
        )

        # Convert encodings to BatchEncoding format
        tokens_and_encodings = [
            self._convert_encoding(
                encoding=encoding,
                return_token_type_ids=return_token_type_ids,
                return_attention_mask=return_attention_mask,
                return_overflowing_tokens=return_overflowing_tokens,
                return_special_tokens_mask=return_special_tokens_mask,
                return_offsets_mapping=return_offsets_mapping,
                return_length=return_length,
                verbose=verbose,
            )
            for encoding in encodings
        ]

        # Convert the output to have dict[list] from list[dict]
        sanitized_tokens = {}
        for key in tokens_and_encodings[0][0]:
            stack = [e for item, _ in tokens_and_encodings for e in item[key]]
            sanitized_tokens[key] = stack
        sanitized_encodings = [e for _, item in tokens_and_encodings for e in item]

        # If returning overflowing tokens, we need to return a mapping
        if return_overflowing_tokens:
            overflow_to_sample_mapping = []
            for i, (toks, _) in enumerate(tokens_and_encodings):
                overflow_to_sample_mapping += [i] * len(toks["input_ids"])
            sanitized_tokens["overflow_to_sample_mapping"] = overflow_to_sample_mapping

        for input_ids in sanitized_tokens["input_ids"]:
            self._eventual_warn_about_too_long_sequence(input_ids, max_length, verbose)

        batched_output = BatchEncoding(sanitized_tokens, sanitized_encodings, tensor_type=return_tensors)

        # If single input, remove the batch dimension (unless returning overflowing tokens)
        if not is_batched and return_tensors is None and not return_overflowing_tokens:
            batched_output = BatchEncoding(
                {
                    key: (value[0] if len(value) > 0 and isinstance(value[0], list) else value)
                    for key, value in batched_output.items()
                },
                batched_output.encodings,
            )

        return batched_output