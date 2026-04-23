def filter_data(self) -> list[Data]:
        # Extract inputs
        input_data: list[Data] = self.input_data
        filter_key: str = self.filter_key.text
        filter_value: str = self.filter_value.text
        operator: str = self.operator

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
            if isinstance(item.data, dict) and filter_key in item.data:
                if self.compare_values(item.data[filter_key], filter_value, operator):
                    filtered_data.append(item)
            else:
                self.status = f"Warning: Some items don't have the key '{filter_key}' or are not dictionaries."

        self.status = filtered_data
        return filtered_data