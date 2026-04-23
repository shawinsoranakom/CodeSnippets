def select_keys(self, *, evaluate: bool | None = None) -> Data:
        """Select specific keys from the data dictionary."""
        self.validate_single_data("Select Keys")
        data_dict = self.get_normalized_data()
        filter_criteria: list[str] = self.select_keys_input

        # Filter the data
        if len(filter_criteria) == 1 and filter_criteria[0] == "data":
            filtered = data_dict["data"]
        else:
            if not all(key in data_dict for key in filter_criteria):
                msg = f"Select key not found in data. Available keys: {list(data_dict.keys())}"
                raise ValueError(msg)
            filtered = {key: value for key, value in data_dict.items() if key in filter_criteria}

        # Create a new Data object with the filtered data
        if evaluate:
            filtered = self.recursive_eval(filtered)

        # Return a new Data object with the filtered data directly in the data attribute
        return Data(data=filtered)