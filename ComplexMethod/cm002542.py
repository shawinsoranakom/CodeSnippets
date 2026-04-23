def __call__(
        self,
        text: TextInput | EncodedInput | list[TextInput] | list[EncodedInput] | None = None,
        text_pair: None = None,
        text_target: None = None,
        text_pair_target: None = None,
        add_special_tokens: bool = True,
        padding: bool | str | PaddingStrategy = False,
        truncation: bool | str | TruncationStrategy | None = None,
        max_length: int | None = None,
        stride: int = 0,
        pad_to_multiple_of: int | None = None,
        padding_side: str | None = None,
        return_tensors: str | TensorType | None = None,
        return_attention_mask: bool | None = None,
        return_overflowing_tokens: bool = False,
        return_special_tokens_mask: bool = False,
        return_length: bool = False,
        verbose: bool = True,
        return_offsets_mapping: Literal[False] = False,
        split_special_tokens: Literal[False] = False,
        **kwargs,
    ) -> BatchEncoding:
        """
        Main method to tokenize and prepare for the model one or several sequence(s) or one or several pair(s) of
        sequences.

        Args:
            text (`str`, `list[str]`, `list[list[str]]`, *optional*):
                The sequence or batch of sequences to be encoded. Each sequence can be a string or a list of int
                (encoded strings).
            text_pair (`None`, *optional*):
                Not supported by `MistralCommonBackend`. Kept to match the signature of `PreTrainedTokenizerBase.__call__`.
            text_target (`None`, *optional*):
                Not supported by `MistralCommonBackend`. Kept to match the signature of `PreTrainedTokenizerBase.__call__`.
            text_pair_target (`None`, *optional*):
                Not supported by `MistralCommonBackend`. Kept to match the signature of `PreTrainedTokenizerBase.__call__`.
        """
        if return_offsets_mapping or split_special_tokens:
            raise ValueError(
                "`MistralCommonBackend` does not support `return_offsets_mapping` and `split_special_tokens`."
            )

        if truncation in [TruncationStrategy.ONLY_FIRST, TruncationStrategy.ONLY_SECOND, "only_first", "only_second"]:
            raise ValueError(
                "Truncation strategy `only_first` and `only_second` are not supported by `MistralCommonBackend`."
            )

        if kwargs:
            raise ValueError(f"Kwargs {list(kwargs.keys())} are not supported by `MistralCommonBackend.__call__`.")

        if text_pair or text_target or text_pair_target:
            raise ValueError(
                "`text_pair`, `text_target` and `text_pair_target` are not supported by `MistralCommonBackend`."
            )

        return super().__call__(
            text=text,
            text_pair=text_pair,
            text_target=text_target,
            add_special_tokens=add_special_tokens,
            padding=padding,
            truncation=truncation,
            max_length=max_length,
            stride=stride,
            pad_to_multiple_of=pad_to_multiple_of,
            padding_side=padding_side,
            return_tensors=return_tensors,
            return_attention_mask=return_attention_mask,
            return_overflowing_tokens=return_overflowing_tokens,
            return_special_tokens_mask=return_special_tokens_mask,
            return_length=return_length,
            verbose=verbose,
        )