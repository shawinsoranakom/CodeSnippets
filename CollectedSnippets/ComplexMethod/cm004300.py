def prepare_for_model(
        self,
        raw_table: "pd.DataFrame",
        raw_query: TextInput | PreTokenizedInput | EncodedInput,
        tokenized_table: TokenizedTable | None = None,
        query_tokens: TokenizedTable | None = None,
        answer_coordinates: list[tuple] | None = None,
        answer_text: list[TextInput] | None = None,
        add_special_tokens: bool = True,
        padding: bool | str | PaddingStrategy = False,
        truncation: bool | str | TapasTruncationStrategy = False,
        max_length: int | None = None,
        pad_to_multiple_of: int | None = None,
        padding_side: str | None = None,
        return_tensors: str | TensorType | None = None,
        return_token_type_ids: bool | None = True,
        return_attention_mask: bool | None = True,
        return_special_tokens_mask: bool = False,
        return_offsets_mapping: bool = False,
        return_length: bool = False,
        verbose: bool = True,
        prepend_batch_axis: bool = False,
        **kwargs,
    ) -> BatchEncoding:
        """
        Prepares a sequence of input id so that it can be used by the model. It adds special tokens, truncates
        sequences if overflowing while taking into account the special tokens.

        Args:
            raw_table (`pd.DataFrame`):
                The original table before any transformation (like tokenization) was applied to it.
            raw_query (`TextInput` or `PreTokenizedInput` or `EncodedInput`):
                The original query before any transformation (like tokenization) was applied to it.
            tokenized_table (`TokenizedTable`):
                The table after tokenization.
            query_tokens (`list[str]`):
                The query after tokenization.
            answer_coordinates (`list[Tuple]` or `list[list[Tuple]]`, *optional*):
                Answer coordinates of each table-question pair in the batch. The answer_coordinates must be a single
                list of one or more tuples. Each tuple must be a (row_index, column_index) pair. The first data row
                (not the column header row) has index 0. The first column has index 0.
            answer_text (`list[str]` or `list[list[str]]`, *optional*):
                Answer text of each table-question pair in the batch. The answer_text must be a single list of one or
                more strings. Each string must be the answer text of a corresponding answer coordinate.
        """
        if isinstance(padding, bool):
            if padding and (max_length is not None or pad_to_multiple_of is not None):
                padding = PaddingStrategy.MAX_LENGTH
            else:
                padding = PaddingStrategy.DO_NOT_PAD
        elif not isinstance(padding, PaddingStrategy):
            padding = PaddingStrategy(padding)

        if isinstance(truncation, bool):
            if truncation:
                truncation = TapasTruncationStrategy.DROP_ROWS_TO_FIT
            else:
                truncation = TapasTruncationStrategy.DO_NOT_TRUNCATE
        elif not isinstance(truncation, TapasTruncationStrategy):
            truncation = TapasTruncationStrategy(truncation)

        encoded_inputs = {}

        is_part_of_batch = False
        prev_answer_coordinates, prev_answer_text = None, None
        if "prev_answer_coordinates" in kwargs and "prev_answer_text" in kwargs:
            is_part_of_batch = True
            prev_answer_coordinates = kwargs["prev_answer_coordinates"]
            prev_answer_text = kwargs["prev_answer_text"]

        num_rows = self._get_num_rows(raw_table, truncation != TapasTruncationStrategy.DO_NOT_TRUNCATE)
        num_columns = self._get_num_columns(raw_table)
        _, _, num_tokens = self._get_table_boundaries(tokenized_table)

        if truncation != TapasTruncationStrategy.DO_NOT_TRUNCATE:
            num_rows, num_tokens = self._get_truncated_table_rows(
                query_tokens, tokenized_table, num_rows, num_columns, max_length, truncation_strategy=truncation
            )
        table_data = list(self._get_table_values(tokenized_table, num_columns, num_rows, num_tokens))

        query_ids = self.convert_tokens_to_ids(query_tokens)
        table_ids = list(zip(*table_data))[0] if len(table_data) > 0 else list(zip(*table_data))
        table_ids = self.convert_tokens_to_ids(list(table_ids))

        if "return_overflowing_tokens" in kwargs and kwargs["return_overflowing_tokens"]:
            raise ValueError("TAPAS does not return overflowing tokens as it works on tables.")

        if add_special_tokens:
            input_ids = self.build_inputs_with_special_tokens(query_ids, table_ids)
        else:
            input_ids = query_ids + table_ids

        if max_length is not None and len(input_ids) > max_length:
            raise ValueError(
                "Could not encode the query and table header given the maximum length. Encoding the query and table "
                f"header results in a length of {len(input_ids)} which is higher than the max_length of {max_length}"
            )

        encoded_inputs["input_ids"] = input_ids

        segment_ids = self.create_segment_token_type_ids_from_sequences(query_ids, table_data)
        column_ids = self.create_column_token_type_ids_from_sequences(query_ids, table_data)
        row_ids = self.create_row_token_type_ids_from_sequences(query_ids, table_data)
        if not is_part_of_batch or (prev_answer_coordinates is None and prev_answer_text is None):
            # simply set the prev_labels to zeros
            prev_labels = [0] * len(row_ids)
        else:
            prev_labels = self.get_answer_ids(
                column_ids, row_ids, table_data, prev_answer_text, prev_answer_coordinates
            )

        # FIRST: parse both the table and question in terms of numeric values

        raw_table = add_numeric_table_values(raw_table)
        raw_query = add_numeric_values_to_question(raw_query)

        # SECOND: add numeric-related features (and not parse them in these functions):

        column_ranks, inv_column_ranks = self._get_numeric_column_ranks(column_ids, row_ids, raw_table)
        numeric_relations = self._get_numeric_relations(raw_query, column_ids, row_ids, raw_table)

        # Load from model defaults
        if return_token_type_ids is None:
            return_token_type_ids = "token_type_ids" in self.model_input_names
        if return_attention_mask is None:
            return_attention_mask = "attention_mask" in self.model_input_names

        if return_attention_mask:
            attention_mask = self.create_attention_mask_from_sequences(query_ids, table_data)
            encoded_inputs["attention_mask"] = attention_mask

        if answer_coordinates is not None and answer_text is not None:
            labels = self.get_answer_ids(column_ids, row_ids, table_data, answer_text, answer_coordinates)
            numeric_values = self._get_numeric_values(raw_table, column_ids, row_ids)
            numeric_values_scale = self._get_numeric_values_scale(raw_table, column_ids, row_ids)

            encoded_inputs["labels"] = labels
            encoded_inputs["numeric_values"] = numeric_values
            encoded_inputs["numeric_values_scale"] = numeric_values_scale

        if return_token_type_ids:
            token_type_ids = [
                segment_ids,
                column_ids,
                row_ids,
                prev_labels,
                column_ranks,
                inv_column_ranks,
                numeric_relations,
            ]

            token_type_ids = [list(ids) for ids in list(zip(*token_type_ids))]
            encoded_inputs["token_type_ids"] = token_type_ids

        if return_special_tokens_mask:
            if add_special_tokens:
                encoded_inputs["special_tokens_mask"] = self.get_special_tokens_mask(query_ids, table_ids)
            else:
                encoded_inputs["special_tokens_mask"] = [0] * len(input_ids)

        # Check lengths
        if max_length is None and len(encoded_inputs["input_ids"]) > self.model_max_length and verbose:
            if not self.deprecation_warnings.get("sequence-length-is-longer-than-the-specified-maximum", False):
                logger.warning(
                    "Token indices sequence length is longer than the specified maximum sequence length "
                    f"for this model ({len(encoded_inputs['input_ids'])} > {self.model_max_length}). Running this "
                    "sequence through the model will result in indexing errors."
                )
            self.deprecation_warnings["sequence-length-is-longer-than-the-specified-maximum"] = True

        # Padding
        if padding != PaddingStrategy.DO_NOT_PAD or return_attention_mask:
            encoded_inputs = self.pad(
                encoded_inputs,
                max_length=max_length,
                padding=padding.value,
                pad_to_multiple_of=pad_to_multiple_of,
                padding_side=padding_side,
                return_attention_mask=return_attention_mask,
            )

        if return_length:
            encoded_inputs["length"] = len(encoded_inputs["input_ids"])

        batch_outputs = BatchEncoding(
            encoded_inputs, tensor_type=return_tensors, prepend_batch_axis=prepend_batch_axis
        )

        return batch_outputs