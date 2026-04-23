def __call__(
        self,
        text: TextInput | PreTokenizedInput | list[TextInput] | list[PreTokenizedInput] | None = None,
        text_pair: TextInput | PreTokenizedInput | list[TextInput] | list[PreTokenizedInput] | None = None,
        text_target: TextInput | PreTokenizedInput | list[TextInput] | list[PreTokenizedInput] | None = None,
        text_pair_target: TextInput | PreTokenizedInput | list[TextInput] | list[PreTokenizedInput] | None = None,
        add_special_tokens: bool = True,
        padding: bool | str | PaddingStrategy = False,
        truncation: bool | str | TruncationStrategy | None = None,
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
        return_offsets_mapping: bool = False,
        return_length: bool = False,
        verbose: bool = True,
        tokenizer_kwargs: dict[str, Any] | None = None,
        **kwargs,
    ) -> BatchEncoding:
        """
        Main method to tokenize and prepare for the model one or several sequence(s) or one or several pair(s) of
        sequences.

        Args:
            text (`str`, `list[str]`, `list[list[str]]`, *optional*):
                The sequence or batch of sequences to be encoded. Each sequence can be a string or a list of strings
                (pretokenized string). If the sequences are provided as list of strings (pretokenized), you must set
                `is_split_into_words=True` (to lift the ambiguity with a batch of sequences).
            text_pair (`str`, `list[str]`, `list[list[str]]`, *optional*):
                The sequence or batch of sequences to be encoded. Each sequence can be a string or a list of strings
                (pretokenized string). If the sequences are provided as list of strings (pretokenized), you must set
                `is_split_into_words=True` (to lift the ambiguity with a batch of sequences).
            text_target (`str`, `list[str]`, `list[list[str]]`, *optional*):
                The sequence or batch of sequences to be encoded as target texts. Each sequence can be a string or a
                list of strings (pretokenized string). If the sequences are provided as list of strings (pretokenized),
                you must set `is_split_into_words=True` (to lift the ambiguity with a batch of sequences).
            text_pair_target (`str`, `list[str]`, `list[list[str]]`, *optional*):
                The sequence or batch of sequences to be encoded as target texts. Each sequence can be a string or a
                list of strings (pretokenized string). If the sequences are provided as list of strings (pretokenized),
                you must set `is_split_into_words=True` (to lift the ambiguity with a batch of sequences).
            tokenizer_kwargs (`dict[str, Any]`, *optional*):
                Additional kwargs to pass to the tokenizer. These will be merged with the explicit parameters and
                other kwargs, with explicit parameters taking precedence.
        """
        # To avoid duplicating
        all_kwargs = {
            "add_special_tokens": add_special_tokens,
            "padding": padding,
            "truncation": truncation,
            "max_length": max_length,
            "stride": stride,
            "is_split_into_words": is_split_into_words,
            "pad_to_multiple_of": pad_to_multiple_of,
            "padding_side": padding_side,
            "return_tensors": return_tensors,
            "return_token_type_ids": return_token_type_ids,
            "return_attention_mask": return_attention_mask,
            "return_overflowing_tokens": return_overflowing_tokens,
            "return_special_tokens_mask": return_special_tokens_mask,
            "return_offsets_mapping": return_offsets_mapping,
            "return_length": return_length,
            "split_special_tokens": kwargs.pop("split_special_tokens", self.split_special_tokens),
            "verbose": verbose,
        }

        max_target_length = kwargs.pop("max_target_length", None)

        # First merge tokenizer_kwargs, then other kwargs (explicit params take precedence)
        if tokenizer_kwargs is not None:
            all_kwargs.update(tokenizer_kwargs)
        all_kwargs.update(kwargs)
        if text is None and text_target is None:
            raise ValueError("You need to specify either `text` or `text_target`.")

        padding_strategy, truncation_strategy, max_length, kwargs = self._get_padding_truncation_strategies(
            padding=all_kwargs.pop("padding", False),
            truncation=all_kwargs.pop("truncation", None),
            max_length=all_kwargs.pop("max_length", None),
            pad_to_multiple_of=all_kwargs.get("pad_to_multiple_of"),
            verbose=all_kwargs.get("verbose", True),
            **kwargs,
        )

        if text is not None:
            # The context manager will send the inputs as normal texts and not text_target, but we shouldn't change the
            # input mode in this case.
            if not self._in_target_context_manager and hasattr(self, "_switch_to_input_mode"):
                self._switch_to_input_mode()
            encodings = self._encode_plus(
                text=text,
                text_pair=text_pair,
                padding_strategy=padding_strategy,
                truncation_strategy=truncation_strategy,
                max_length=max_length,
                **all_kwargs,
            )
        if text_target is not None:
            if hasattr(self, "_switch_to_target_mode"):
                self._switch_to_target_mode()
            target_encodings = self._encode_plus(
                text=text_target,
                text_pair=text_pair_target,
                padding_strategy=padding_strategy,
                truncation_strategy=truncation_strategy,
                max_length=max_target_length if max_target_length is not None else max_length,
                **all_kwargs,
            )
            # Leave back tokenizer in input mode
            if hasattr(self, "_switch_to_input_mode"):
                self._switch_to_input_mode()

        if text_target is None:
            return encodings
        elif text is None:
            return target_encodings
        else:
            encodings["labels"] = target_encodings["input_ids"]
            return encodings