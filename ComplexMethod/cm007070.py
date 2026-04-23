def combine_data(self, *, evaluate: bool | None = None) -> Data:
        """Combine multiple data objects into one."""
        logger.info("combining data")
        if not self.data_is_list():
            return self.data[0] if self.data else Data(data={})

        if len(self.data) == 1:
            msg = "Combine operation requires multiple data inputs."
            raise ValueError(msg)

        data_dicts = [data.model_dump().get("data", data.model_dump()) for data in self.data]
        combined_data = {}

        for data_dict in data_dicts:
            for key, value in data_dict.items():
                if key not in combined_data:
                    combined_data[key] = value
                elif isinstance(combined_data[key], list):
                    if isinstance(value, list):
                        combined_data[key].extend(value)
                    else:
                        combined_data[key].append(value)
                else:
                    # If current value is not a list, convert it to list and add new value
                    combined_data[key] = (
                        [combined_data[key], value] if not isinstance(value, list) else [combined_data[key], *value]
                    )

        if evaluate:
            combined_data = self.recursive_eval(combined_data)

        return Data(**combined_data)