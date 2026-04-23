def batch_encode_plus(
        self,
        table: "pd.DataFrame",
        queries: list[TextInput] | list[PreTokenizedInput] | list[EncodedInput] | None = None,
        answer_coordinates: list[list[tuple]] | None = None,
        answer_text: list[list[TextInput]] | None = None,
        add_special_tokens: bool = True,
        padding: bool | str | PaddingStrategy = False,
        truncation: bool | str | TapasTruncationStrategy = False,
        max_length: int | None = None,
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
        Prepare a table and a list of strings for the model.

        <Tip warning={true}>

        This method is deprecated, `__call__` should be used instead.

        </Tip>

        Args:
            table (`pd.DataFrame`):
                Table containing tabular data. Note that all cell values must be text. Use *.astype(str)* on a Pandas
                dataframe to convert it to string.
            queries (`list[str]`):
                Batch of questions related to a table to be encoded. Note that all questions must refer to the **same**
                table.
            answer_coordinates (`list[Tuple]` or `list[list[Tuple]]`, *optional*):
                Answer coordinates of each table-question pair in the batch. Each tuple must be a (row_index,
                column_index) pair. The first data row (not the column header row) has index 0. The first column has
                index 0. The answer_coordinates must be a list of lists of tuples (each list corresponding to a single
                table-question pair).
            answer_text (`list[str]` or `list[list[str]]`, *optional*):
                Answer text of each table-question pair in the batch. In case a batch of table-question pairs is
                provided, then the answer_coordinates must be a list of lists of strings (each list corresponding to a
                single table-question pair). Each string must be the answer text of a corresponding answer coordinate.
        """
        if return_token_type_ids is not None and not add_special_tokens:
            raise ValueError(
                "Asking to return token_type_ids while setting add_special_tokens to False "
                "results in an undefined behavior. Please set add_special_tokens to True or "
                "set return_token_type_ids to None."
            )

        if (answer_coordinates and not answer_text) or (not answer_coordinates and answer_text):
            raise ValueError("In case you provide answers, both answer_coordinates and answer_text should be provided")
        elif answer_coordinates is None and answer_text is None:
            answer_coordinates = answer_text = [None] * len(queries)

        if "is_split_into_words" in kwargs:
            raise NotImplementedError("Currently TapasTokenizer only supports questions as strings.")

        if return_offsets_mapping:
            raise NotImplementedError(
                "return_offset_mapping is not available when using Python tokenizers. "
                "To use this feature, change your tokenizer to one deriving from "
                "transformers.PreTrainedTokenizerFast."
            )

        return self._batch_encode_plus(
            table=table,
            queries=queries,
            answer_coordinates=answer_coordinates,
            answer_text=answer_text,
            add_special_tokens=add_special_tokens,
            padding=padding,
            truncation=truncation,
            max_length=max_length,
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