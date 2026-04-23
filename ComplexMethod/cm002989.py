def __call__(
        self,
        text: TextInput | PreTokenizedInput | list[TextInput] | list[PreTokenizedInput],
        text_pair: PreTokenizedInput | list[PreTokenizedInput] | None = None,
        boxes: list[list[int]] | list[list[list[int]]] | None = None,
        word_labels: list[int] | list[list[int]] | None = None,
        add_special_tokens: bool = True,
        padding: bool | str | PaddingStrategy = False,
        truncation: bool | str | TruncationStrategy = None,
        max_length: int | None = None,
        stride: int = 0,
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
        """
        Main method to tokenize and prepare for the model one or several sequence(s) or one or several pair(s) of
        sequences with word-level normalized bounding boxes and optional labels.

        Args:
            text (`str`, `List[str]`, `List[List[str]]`):
                The sequence or batch of sequences to be encoded. Each sequence can be a string, a list of strings
                (words of a single example or questions of a batch of examples) or a list of list of strings (batch of
                words).
            text_pair (`List[str]`, `List[List[str]]`):
                The sequence or batch of sequences to be encoded. Each sequence should be a list of strings
                (pretokenized string).
            boxes (`List[List[int]]`, `List[List[List[int]]]`):
                Word-level bounding boxes. Each bounding box should be normalized to be on a 0-1000 scale.
            word_labels (`List[int]`, `List[List[int]]`, *optional*):
                Word-level integer labels (for token classification tasks such as FUNSD, CORD).
        """

        # Input type checking for clearer error
        def _is_valid_text_input(t):
            if isinstance(t, str):
                # Strings are fine
                return True
            elif isinstance(t, (list, tuple)):
                # List are fine as long as they are...
                if len(t) == 0:
                    # ... empty
                    return True
                elif isinstance(t[0], str):
                    # ... list of strings
                    return True
                elif isinstance(t[0], (list, tuple)):
                    # ... list with an empty list or with a list of strings
                    return len(t[0]) == 0 or isinstance(t[0][0], str)
                else:
                    return False
            else:
                return False

        if text_pair is not None:
            # in case text + text_pair are provided, text = questions, text_pair = words
            if not _is_valid_text_input(text):
                raise ValueError("text input must of type `str` (single example) or `List[str]` (batch of examples). ")
            if not isinstance(text_pair, (list, tuple)):
                raise ValueError(
                    "Words must be of type `List[str]` (single pretokenized example), "
                    "or `List[List[str]]` (batch of pretokenized examples)."
                )
        else:
            # in case only text is provided => must be words
            if not isinstance(text, (list, tuple)):
                raise ValueError(
                    "Words must be of type `List[str]` (single pretokenized example), "
                    "or `List[List[str]]` (batch of pretokenized examples)."
                )

        if text_pair is not None:
            is_batched = isinstance(text, (list, tuple))
        else:
            is_batched = isinstance(text, (list, tuple)) and text and isinstance(text[0], (list, tuple))

        words = text if text_pair is None else text_pair
        if boxes is None:
            raise ValueError("You must provide corresponding bounding boxes")
        if is_batched:
            if len(words) != len(boxes):
                raise ValueError("You must provide words and boxes for an equal amount of examples")
            for words_example, boxes_example in zip(words, boxes):
                if len(words_example) != len(boxes_example):
                    raise ValueError("You must provide as many words as there are bounding boxes")
        else:
            if len(words) != len(boxes):
                raise ValueError("You must provide as many words as there are bounding boxes")

        if is_batched:
            if text_pair is not None and len(text) != len(text_pair):
                raise ValueError(
                    f"batch length of `text`: {len(text)} does not match batch length of `text_pair`:"
                    f" {len(text_pair)}."
                )
            batch_text_or_text_pairs = list(zip(text, text_pair)) if text_pair is not None else text
            is_pair = bool(text_pair is not None)
            return self.batch_encode_plus(
                batch_text_or_text_pairs=batch_text_or_text_pairs,
                is_pair=is_pair,
                boxes=boxes,
                word_labels=word_labels,
                add_special_tokens=add_special_tokens,
                padding=padding,
                truncation=truncation,
                max_length=max_length,
                stride=stride,
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
            return self.encode_plus(
                text=text,
                text_pair=text_pair,
                boxes=boxes,
                word_labels=word_labels,
                add_special_tokens=add_special_tokens,
                padding=padding,
                truncation=truncation,
                max_length=max_length,
                stride=stride,
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