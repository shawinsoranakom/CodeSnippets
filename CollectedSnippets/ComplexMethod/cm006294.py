def _convert_to_opik_type(self, value):
        """Recursively converts a value to a Opik compatible type."""
        if isinstance(value, dict):
            value = {key: self._convert_to_opik_type(val) for key, val in value.items()}

        elif isinstance(value, list):
            value = [self._convert_to_opik_type(v) for v in value]

        elif isinstance(value, Message):
            value = value.text

        elif isinstance(value, Data):
            value = value.get_text()

        elif isinstance(value, (BaseMessage | HumanMessage | SystemMessage)):
            value = value.content

        elif isinstance(value, Document):
            value = value.page_content

        elif isinstance(value, (types.GeneratorType | types.NoneType)):
            value = str(value)

        return value