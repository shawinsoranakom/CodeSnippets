def _get_numeric_values(self, table, column_ids, row_ids):
        """Returns numeric values for computation of answer loss."""

        numeric_values = [float("nan")] * len(column_ids)

        if table is not None:
            num_rows = table.shape[0]
            num_columns = table.shape[1]

            for col_index in range(num_columns):
                for row_index in range(num_rows):
                    numeric_value = table.iloc[row_index, col_index].numeric_value
                    if numeric_value is not None:
                        if numeric_value.float_value is None:
                            continue
                        float_value = numeric_value.float_value
                        if float_value == float("inf"):
                            continue
                        for index in self._get_cell_token_indexes(column_ids, row_ids, col_index, row_index):
                            numeric_values[index] = float_value

        return numeric_values