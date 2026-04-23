def to_data(self, data: Any, *, keys: list[str] | None = None, silent_errors: bool = False) -> list[Data]:
        """Converts input data into a list of Data objects.

        Args:
            data (Any): The input data to be converted. It can be a single item or a sequence of items.
                If the input data is a Langchain Document, text_key and data_key are ignored.

            keys (List[str], optional): The keys to access the text and data values in each item.
                It should be a list of strings where the first element is the text key and the second element
                is the data key.
                Defaults to None, in which case the default keys "text" and "data" are used.
            silent_errors (bool, optional): Whether to suppress errors when the specified keys are not found
                in the data.

        Returns:
            List[Data]: A list of Data objects.

        Raises:
            ValueError: If the input data is not of a valid type or if the specified keys are not found in the data.

        """
        if not keys:
            keys = []
        data_objects = []
        if not isinstance(data, Sequence):
            data = [data]
        for item in data:
            data_dict = {}
            if isinstance(item, Document):
                data_dict = item.metadata
                data_dict["text"] = item.page_content
            elif isinstance(item, BaseModel):
                model_dump = item.model_dump()
                for key in keys:
                    if silent_errors:
                        data_dict[key] = model_dump.get(key, "")
                    else:
                        try:
                            data_dict[key] = model_dump[key]
                        except KeyError as e:
                            msg = f"Key {key} not found in {item}"
                            raise ValueError(msg) from e

            elif isinstance(item, str):
                data_dict = {"text": item}
            elif isinstance(item, dict):
                data_dict = item.copy()
            else:
                msg = f"Invalid data type: {type(item)}"
                raise TypeError(msg)

            data_objects.append(Data(data=data_dict))

        return data_objects