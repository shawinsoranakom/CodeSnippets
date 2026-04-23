def filter_rows_by_value(self, df: DataFrame) -> DataFrame:
        column = df[self.column_name]
        filter_value = self.filter_value

        # Handle regular DropdownInput format (just a string value)
        operator = getattr(self, "filter_operator", "equals")  # Default to equals for backward compatibility

        if operator == "equals":
            mask = column == filter_value
        elif operator == "not equals":
            mask = column != filter_value
        elif operator == "contains":
            mask = column.astype(str).str.contains(str(filter_value), na=False)
        elif operator == "not contains":
            mask = ~column.astype(str).str.contains(str(filter_value), na=False)
        elif operator == "starts with":
            mask = column.astype(str).str.startswith(str(filter_value), na=False)
        elif operator == "ends with":
            mask = column.astype(str).str.endswith(str(filter_value), na=False)
        elif operator == "greater than":
            try:
                # Try to convert filter_value to numeric for comparison
                numeric_value = pd.to_numeric(filter_value)
                mask = column > numeric_value
            except (ValueError, TypeError):
                # If conversion fails, compare as strings
                mask = column.astype(str) > str(filter_value)
        elif operator == "less than":
            try:
                # Try to convert filter_value to numeric for comparison
                numeric_value = pd.to_numeric(filter_value)
                mask = column < numeric_value
            except (ValueError, TypeError):
                # If conversion fails, compare as strings
                mask = column.astype(str) < str(filter_value)
        else:
            mask = column == filter_value  # Fallback to equals

        return DataFrame(df[mask])