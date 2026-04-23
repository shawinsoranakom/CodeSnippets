def _get_input_type_name(self) -> str:
        """Detect and return the input type name for error messages."""
        if isinstance(self.data, Message):
            return "Message"
        if isinstance(self.data, DataFrame):
            return "DataFrame"
        if isinstance(self.data, Data):
            return "Data"
        if isinstance(self.data, list) and len(self.data) > 0:
            first = self.data[0]
            if isinstance(first, Message):
                return "Message"
            if isinstance(first, DataFrame):
                return "DataFrame"
            if isinstance(first, Data):
                return "Data"
        return "unknown"