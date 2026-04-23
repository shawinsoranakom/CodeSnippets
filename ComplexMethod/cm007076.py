def perform_operation(self) -> DataFrame:
        # Handle SortableListInput format for operation (also supports legacy string format)
        operation_input = getattr(self, "operation", [])
        if isinstance(operation_input, list):
            op = operation_input[0].get("name", "") if operation_input else ""
        else:
            op = operation_input or ""

        # Merge and Concatenate use their own inputs, not the primary df
        if op == "Merge":
            return self.merge_dataframes()
        if op == "Concatenate":
            return self.concatenate_dataframes()

        df_copy = self._get_primary_dataframe()

        # If no operation selected, return original DataFrame
        if not op:
            return df_copy

        if op == "Filter":
            return self.filter_rows_by_value(df_copy)
        if op == "Sort":
            return self.sort_by_column(df_copy)
        if op == "Drop Column":
            return self.drop_column(df_copy)
        if op == "Rename Column":
            return self.rename_column(df_copy)
        if op == "Add Column":
            return self.add_column(df_copy)
        if op == "Select Columns":
            return self.select_columns(df_copy)
        if op == "Head":
            return self.head(df_copy)
        if op == "Tail":
            return self.tail(df_copy)
        if op == "Replace Value":
            return self.replace_values(df_copy)
        if op == "Drop Duplicates":
            return self.drop_duplicates(df_copy)
        msg = f"Unsupported operation: {op}"
        logger.error(msg)
        raise ValueError(msg)