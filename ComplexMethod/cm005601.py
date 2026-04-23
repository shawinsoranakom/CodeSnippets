def __call__(self, inputs: str | list[str], **kwargs):
        is_split_into_words = kwargs.get("is_split_into_words", False)
        delimiter = kwargs.get("delimiter")

        if inputs is not None and isinstance(inputs, (list, tuple)) and len(inputs) > 0:
            inputs = list(inputs)
            batch_size = len(inputs)
        elif isinstance(inputs, str):
            inputs = [inputs]
            batch_size = 1
        elif Dataset is not None and isinstance(inputs, Dataset) or isinstance(inputs, types.GeneratorType):
            return inputs, is_split_into_words, None, delimiter
        else:
            raise ValueError("At least one input is required.")

        offset_mapping = kwargs.get("offset_mapping")
        if offset_mapping:
            if isinstance(offset_mapping, list) and isinstance(offset_mapping[0], tuple):
                offset_mapping = [offset_mapping]
            if len(offset_mapping) != batch_size:
                raise ValueError("offset_mapping should have the same batch size as the input")
        return inputs, is_split_into_words, offset_mapping, delimiter