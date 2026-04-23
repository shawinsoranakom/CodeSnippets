def __call__(
        self,
        table: Union["pd.DataFrame", TextInput, list[TextInput], None],
        queries: TextInput
        | PreTokenizedInput
        | EncodedInput
        | list[TextInput]
        | list[PreTokenizedInput]
        | list[EncodedInput]
        | None = None,
        answer_coordinates: list[tuple] | list[list[tuple]] | None = None,
        answer_text: list[TextInput] | list[list[TextInput]] | None = None,
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
        Main method to tokenize and prepare for the model one or several sequence(s) related to a table.

        Args:
            table (`pd.DataFrame` or `str` or `list[str]`):
                Table containing tabular data. Note that all cell values must be text. Use *.astype(str)* on a Pandas
                dataframe to convert it to string. When passing a string or list of strings, those will be interpreted
                as queries with an empty table (to support generic tokenizer tests).
            queries (`str` or `list[str]`):
                Question or batch of questions related to a table to be encoded. Note that in case of a batch, all
                questions must refer to the **same** table.
            answer_coordinates (`list[Tuple]` or `list[list[Tuple]]`, *optional*):
                Answer coordinates of each table-question pair in the batch. In case only a single table-question pair
                is provided, then the answer_coordinates must be a single list of one or more tuples. Each tuple must
                be a (row_index, column_index) pair. The first data row (not the column header row) has index 0. The
                first column has index 0. In case a batch of table-question pairs is provided, then the
                answer_coordinates must be a list of lists of tuples (each list corresponding to a single
                table-question pair).
            answer_text (`list[str]` or `list[list[str]]`, *optional*):
                Answer text of each table-question pair in the batch. In case only a single table-question pair is
                provided, then the answer_text must be a single list of one or more strings. Each string must be the
                answer text of a corresponding answer coordinate. In case a batch of table-question pairs is provided,
                then the answer_coordinates must be a list of lists of strings (each list corresponding to a single
                table-question pair).
        """
        if not isinstance(table, pd.DataFrame):
            if queries is not None:
                raise AssertionError("Table must be of type pd.DataFrame when queries are provided separately.")
            inferred_queries = table
            table = pd.DataFrame.from_dict({})
            queries = inferred_queries

        # Input type checking for clearer error
        valid_query = False

        # Check that query has a valid type
        if queries is None or isinstance(queries, str):
            valid_query = True
        elif isinstance(queries, (list, tuple)):
            if len(queries) == 0 or isinstance(queries[0], str):
                valid_query = True

        if not valid_query:
            raise ValueError(
                "queries input must of type `str` (single example), `list[str]` (batch or single pretokenized"
                " example). "
            )
        is_batched = isinstance(queries, (list, tuple))

        if is_batched:
            return self.batch_encode_plus(
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
        else:
            return self.encode_plus(
                table=table,
                query=queries,
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