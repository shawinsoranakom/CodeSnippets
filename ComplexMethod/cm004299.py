def encode_plus(
        self,
        table: Union["pd.DataFrame", TextInput, list[TextInput]],
        query: TextInput | PreTokenizedInput | EncodedInput | None = None,
        answer_coordinates: list[tuple] | None = None,
        answer_text: list[TextInput] | None = None,
        add_special_tokens: bool = True,
        padding: bool | str | PaddingStrategy = False,
        truncation: bool | str | TapasTruncationStrategy = False,
        max_length: int | None = None,
        pad_to_multiple_of: int | None = None,
        padding_side: str | None = None,
        return_tensors: str | TensorType | None = None,
        return_token_type_ids: bool | None = None,
        return_attention_mask: bool | None = None,
        return_special_tokens_mask: bool = False,
        return_offsets_mapping: bool = False,
        return_length: bool = False,
        verbose: bool = True,
        **kwargs,
    ) -> BatchEncoding:
        """
        Prepare a table and a string for the model.

        Args:
            table (`pd.DataFrame` or `str` or `list[str]`):
                Table containing tabular data. When passing a string or list of strings, those will be interpreted as
                queries with an empty table (to support generic tokenizer tests).
            query (`str` or `list[str]`):
                Question related to a table to be encoded.
            answer_coordinates (`list[Tuple]` or `list[list[Tuple]]`, *optional*):
                Answer coordinates of each table-question pair in the batch. The answer_coordinates must be a single
                list of one or more tuples. Each tuple must be a (row_index, column_index) pair. The first data row
                (not the column header row) has index 0. The first column has index 0.
            answer_text (`list[str]` or `list[list[str]]`, *optional*):
                Answer text of each table-question pair in the batch. The answer_text must be a single list of one or
                more strings. Each string must be the answer text of a corresponding answer coordinate.
        """
        if return_token_type_ids is not None and not add_special_tokens:
            raise ValueError(
                "Asking to return token_type_ids while setting add_special_tokens to False "
                "results in an undefined behavior. Please set add_special_tokens to True or "
                "set return_token_type_ids to None."
            )

        if (answer_coordinates and not answer_text) or (not answer_coordinates and answer_text):
            raise ValueError("In case you provide answers, both answer_coordinates and answer_text should be provided")

        if "is_split_into_words" in kwargs:
            raise NotImplementedError("Currently TapasTokenizer only supports questions as strings.")

        if return_offsets_mapping:
            raise NotImplementedError(
                "return_offset_mapping is not available when using Python tokenizers. "
                "To use this feature, change your tokenizer to one deriving from "
                "transformers.PreTrainedTokenizerFast."
            )

        if not isinstance(table, pd.DataFrame):
            if query is not None:
                raise AssertionError("Table must be of type pd.DataFrame when queries are provided separately.")
            inferred_query = table
            table = pd.DataFrame.from_dict({})
            query = inferred_query

        return self._encode_plus(
            table=table,
            query=query,
            answer_coordinates=answer_coordinates,
            answer_text=answer_text,
            add_special_tokens=add_special_tokens,
            truncation=truncation,
            padding=padding,
            max_length=max_length,
            pad_to_multiple_of=pad_to_multiple_of,
            padding_side=padding_side,
            return_tensors=return_tensors,
            return_token_type_ids=return_token_type_ids,
            return_attention_mask=return_attention_mask,
            return_special_tokens_mask=return_special_tokens_mask,
            return_offsets_mapping=return_offsets_mapping,
            return_length=return_length,
            verbose=verbose,
            **kwargs,
        )