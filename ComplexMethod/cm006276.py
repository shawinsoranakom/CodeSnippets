def _convert_to_langchain_type(self, value):
        from langflow.schema.message import Message

        if isinstance(value, dict):
            value = {key: self._convert_to_langchain_type(val) for key, val in value.items()}
        elif isinstance(value, list):
            value = [self._convert_to_langchain_type(v) for v in value]
        elif isinstance(value, Message):
            if "prompt" in value:
                value = value.load_lc_prompt()
            elif value.sender:
                value = value.to_lc_message()
            else:
                value = value.to_lc_document()
        elif isinstance(value, Data):
            value = value.to_lc_document()
        elif isinstance(value, types.GeneratorType):
            # generator is not serializable, also we can't consume it
            value = str(value)
        return value