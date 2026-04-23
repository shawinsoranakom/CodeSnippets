def filter_data(self, input_data: list[dict[str, Any]], filter_key: str, filter_value: str, operator: str) -> list:
        """Filter list data based on key, value, and operator."""
        # Validate inputs
        if not input_data:
            self.status = "Input data is empty."
            return []

        if not filter_key or not filter_value:
            self.status = "Filter key or value is missing."
            return input_data

        # Filter the data
        filtered_data = []
        for item in input_data:
            if isinstance(item, dict) and filter_key in item:
                if self.compare_values(item[filter_key], filter_value, operator):
                    filtered_data.append(item)
            else:
                self.status = f"Warning: Some items don't have the key '{filter_key}' or are not dictionaries."

        return filtered_data