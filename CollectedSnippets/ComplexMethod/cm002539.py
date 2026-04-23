def _encode_plus(  # type: ignore[override]
        self,
        text: TextInput | PreTokenizedInput | EncodedInput,
        text_pair: None = None,
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
        return_offsets_mapping: Literal[False] = False,
        split_special_tokens: Literal[False] = False,
        **kwargs,
    ) -> BatchEncoding:
        # Detect batched inputs (list of sequences)
        if text_pair is not None:
            raise ValueError("`MistralCommonBackend` does not support `text_pair != None` for `_encode_plus`.")

        if return_offsets_mapping or split_special_tokens:
            raise ValueError(
                "`MistralCommonBackend` does not support `return_offsets_mapping` and `split_special_tokens`."
            )

        if kwargs:
            raise ValueError(f"Kwargs {list(kwargs.keys())} are not supported by `MistralCommonBackend._encode_plus`.")

        is_batched = isinstance(text, (list, tuple)) and (
            (not text and not is_split_into_words)
            or (text and is_split_into_words and isinstance(text[0], (list, tuple)))
            or (text and not is_split_into_words and isinstance(text[0], (str, list, tuple)))
        )

        if is_batched:
            batch_outputs = {}
            one_overflowed = False
            for current_text in text:
                current_output = self._encode_plus(
                    text=current_text,
                    text_pair=None,
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
                )
                for key, value in current_output.items():
                    batch_outputs.setdefault(key, []).append(value)

                # To ensure the list is built for each sample, we need to add this.
                if return_overflowing_tokens and not return_tensors:
                    if "overflowing_tokens" not in current_output:
                        batch_outputs.setdefault("overflowing_tokens", []).append([0])
                        batch_outputs.setdefault("num_truncated_tokens", []).append([0])
                    else:
                        one_overflowed = True

            # Remove overflow-related keys before tensor conversion if return_tensors is set
            # Slow tokenizers don't support returning these as tensors
            if return_overflowing_tokens and (return_tensors or not one_overflowed):
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

        def get_input_ids(text):
            if isinstance(text, str):
                return self._text_to_ids(text, False)
            elif isinstance(text, (list, tuple)) and len(text) > 0 and isinstance(text[0], int):
                return text
            else:
                raise ValueError(f"Input {text} is not valid. Should be a string, or a list/tuple of integers.")

        first_ids = get_input_ids(text)

        return self.prepare_for_model(
            first_ids,
            pair_ids=None,
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