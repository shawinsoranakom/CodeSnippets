def _clean_args(self):
        """Prepare arguments based on input type."""
        input_data = self.input_data

        match input_data:
            case list() if all(isinstance(item, Data) for item in input_data):
                msg = "List of Data objects is not supported."
                raise ValueError(msg)
            case DataFrame():
                return input_data, None
            case Data():
                return None, input_data
            case dict() if "data" in input_data:
                try:
                    if "columns" in input_data:  # Likely a DataFrame
                        return DataFrame.from_dict(input_data), None
                    # Likely a Data object
                    return None, Data(**input_data)
                except (TypeError, ValueError, KeyError) as e:
                    msg = f"Invalid structured input provided: {e!s}"
                    raise ValueError(msg) from e
            case _:
                msg = f"Unsupported input type: {type(input_data)}. Expected DataFrame or Data."
                raise ValueError(msg)