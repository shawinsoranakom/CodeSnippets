def merge_data(self, new_data: Data | list[Data] | None) -> list[Data]:
            r"""Generate a new list of Data objects by merging `new_data` into the current `data`.

            Args:
                new_data (Data | list[Data] | None): The new Data object(s) to merge into each existing Data object.
                    If None, the current `data` is returned unchanged.

            Returns:
                list[Data]: A new list of Data objects with `new_data` merged.
            """
            if new_data is None:
                return self.data

            if isinstance(new_data, Data):
                new_data_list = [new_data]
            elif isinstance(new_data, list) and all(isinstance(item, Data) for item in new_data):
                new_data_list = new_data
            else:
                msg = "new_data must be a Data object, a list of Data objects, or None."
                if not self._silent_errors:
                    raise ValueError(msg)
                return self.data

            return [
                Data(data={**data.data, **new_data_item.data}) for data in self.data for new_data_item in new_data_list
            ]