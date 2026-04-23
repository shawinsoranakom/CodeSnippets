def _encode_plus(
        self,
        text: TextInput | PreTokenizedInput | EncodedInput,
        text_pair: TextInput | PreTokenizedInput | EncodedInput | None = None,
        add_special_tokens: bool = True,
        padding_strategy: PaddingStrategy = PaddingStrategy.DO_NOT_PAD,
        truncation_strategy: TruncationStrategy = TruncationStrategy.DO_NOT_TRUNCATE,
        max_length: int | None = None,
        stride: int = 0,
        is_split_into_words: bool = False,
        pad_to_multiple_of: int | None = None,
        padding_side: str | None = None,
        return_tensors: str | TensorType | None = None,
        return_token_type_ids: bool | None = None,
        return_attention_mask: bool | None = None,
        return_overflowing_tokens: bool = False,
        return_special_tokens_mask: bool = False,
        return_length: bool = False,
        verbose: bool = True,
        **kwargs,
    ) -> BatchEncoding:
        # Detect batched inputs (list of sequences)
        is_batched = isinstance(text, (list, tuple)) and (
            (not text and not is_split_into_words)
            or (text and is_split_into_words and isinstance(text[0], (list, tuple)))
            or (text and not is_split_into_words and isinstance(text[0], (str, list, tuple)))
        )

        if is_batched:
            if text_pair is not None:
                if not isinstance(text_pair, (list, tuple)) or len(text_pair) != len(text):
                    raise ValueError("If `text` is a batch, `text_pair` must also be a batch of the same length.")
            pairs = text_pair if text_pair is not None else [None] * len(text)

            batch_outputs = {}
            for current_text, current_pair in zip(text, pairs):
                # Handle tuples/lists as sequence pairs like ("text1", "text2")
                # For is_split_into_words=True: only unpack if it's a tuple of exactly 2 sequences (pair)
                # Otherwise, treat the list as a single pretokenized sequence
                if (
                    isinstance(current_text, (list, tuple))
                    and current_text
                    and not isinstance(current_text[0], int)
                    and current_pair is None
                ):
                    # Check if this looks like a pair: tuple/list of length 2 where elements are strings or lists/tuples
                    is_pair = (
                        len(current_text) == 2
                        and (isinstance(current_text[0], str) or isinstance(current_text[0], (list, tuple)))
                        and (isinstance(current_text[1], str) or isinstance(current_text[1], (list, tuple)))
                    )
                    if is_pair:
                        current_text, current_pair = current_text
                    elif len(current_text) == 1:
                        current_text = current_text[0]
                    elif not is_split_into_words:
                        # Only raise error for non-pretokenized input
                        raise ValueError(f"Expected a pair of sequences, got {len(current_text)} sequences.")

                current_output = self._encode_plus(
                    text=current_text,
                    text_pair=current_pair,
                    add_special_tokens=add_special_tokens,
                    padding_strategy=PaddingStrategy.DO_NOT_PAD,  # we pad in batch afterward
                    truncation_strategy=truncation_strategy,
                    max_length=max_length,
                    stride=stride,
                    is_split_into_words=is_split_into_words,
                    pad_to_multiple_of=None,  # we pad in batch afterward
                    padding_side=None,  # we pad in batch afterward
                    return_tensors=None,  # We convert the whole batch to tensors at the end
                    return_token_type_ids=return_token_type_ids,
                    return_attention_mask=False,  # we pad in batch afterward
                    return_overflowing_tokens=return_overflowing_tokens,
                    return_special_tokens_mask=return_special_tokens_mask,
                    return_length=return_length,
                    verbose=verbose,
                    **kwargs,
                )
                for key, value in current_output.items():
                    batch_outputs.setdefault(key, []).append(value)

            # Remove overflow-related keys before tensor conversion if return_tensors is set
            # Slow tokenizers don't support returning these as tensors
            if return_tensors and return_overflowing_tokens:
                batch_outputs.pop("overflowing_tokens", None)
                batch_outputs.pop("num_truncated_tokens", None)

            batch_outputs = self.pad(
                batch_outputs,
                padding=padding_strategy.value,
                max_length=max_length,
                pad_to_multiple_of=pad_to_multiple_of,
                padding_side=padding_side,
                return_attention_mask=return_attention_mask,
            )

            return BatchEncoding(batch_outputs, tensor_type=return_tensors)

        # Single sequence handling
        def get_input_ids(text):
            if isinstance(text, str):
                # Normal case: tokenize string
                return self.convert_tokens_to_ids(self.tokenize(text, **kwargs))
            if isinstance(text, (list, tuple)) and text:
                if isinstance(text[0], int):
                    return text
                # Pre-tokenized strings
                if isinstance(text[0], str):
                    if is_split_into_words:
                        return self.convert_tokens_to_ids(
                            [tok for word in text for tok in self.tokenize(word, **kwargs)]
                        )
                    return self.convert_tokens_to_ids(text)
            raise ValueError(f"Input must be a string, list of strings, or list of ints, got: {type(text)}")

        first_ids = get_input_ids(text)
        second_ids = get_input_ids(text_pair) if text_pair is not None else None

        return self.prepare_for_model(
            first_ids,
            pair_ids=second_ids,
            add_special_tokens=add_special_tokens,
            padding=padding_strategy.value,
            truncation=truncation_strategy.value,
            max_length=max_length,
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