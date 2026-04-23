def _extract_simple_value(self, value: Any) -> Any:
        """Extract the simplest, most useful value from any input type."""
        # Handle None
        if value is None:
            return None

        # Handle simple types directly
        if isinstance(value, (str, int, float, bool)):
            return value

        # Handle lists and tuples - keep simple
        if isinstance(value, (list, tuple)):
            return [self._extract_simple_value(item) for item in value]

        # Handle dictionaries - keep simple
        if isinstance(value, dict):
            return {str(k): self._extract_simple_value(v) for k, v in value.items()}

        # Handle Message objects - extract only the text
        if hasattr(value, "text"):
            return str(value.text) if value.text is not None else ""

        # Handle Data objects - extract the data content
        if hasattr(value, "data") and value.data is not None:
            return self._extract_simple_value(value.data)

        # For any other object, convert to string
        return str(value)