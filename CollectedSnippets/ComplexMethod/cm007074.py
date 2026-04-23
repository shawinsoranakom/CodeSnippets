def _process_operation(self, operation: DataOperation) -> DataFrame:
        if operation == DataOperation.CONCATENATE:
            combined_data: dict[str, str | object] = {}
            for data_input in self.data_inputs:
                for key, value in data_input.data.items():
                    if key in combined_data:
                        if isinstance(combined_data[key], str) and isinstance(value, str):
                            combined_data[key] = f"{combined_data[key]}\n{value}"
                        else:
                            combined_data[key] = value
                    else:
                        combined_data[key] = value
            return DataFrame([combined_data])

        if operation == DataOperation.APPEND:
            rows = [data_input.data for data_input in self.data_inputs]
            return DataFrame(rows)

        if operation == DataOperation.MERGE:
            result_data: dict[str, str | list[str] | object] = {}
            for data_input in self.data_inputs:
                for key, value in data_input.data.items():
                    if key in result_data and isinstance(value, str):
                        if isinstance(result_data[key], list):
                            cast("list[str]", result_data[key]).append(value)
                        else:
                            result_data[key] = [result_data[key], value]
                    else:
                        result_data[key] = value
            return DataFrame([result_data])

        if operation == DataOperation.JOIN:
            combined_data = {}
            for idx, data_input in enumerate(self.data_inputs, 1):
                for key, value in data_input.data.items():
                    new_key = f"{key}_doc{idx}" if idx > 1 else key
                    combined_data[new_key] = value
            return DataFrame([combined_data])

        return DataFrame()