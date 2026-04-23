def _convert_to_openlayer_type(self, value: Any) -> Any:
        """Convert LangFlow/LangChain types to Openlayer-compatible primitives.

        Args:
            value: Input value to convert

        Returns:
            Converted value suitable for Openlayer ingestion
        """
        if isinstance(value, dict):
            return {key: self._convert_to_openlayer_type(val) for key, val in value.items()}

        if isinstance(value, list):
            return [self._convert_to_openlayer_type(v) for v in value]

        if isinstance(value, Message):
            return value.text

        if isinstance(value, Data):
            return value.get_text()

        if isinstance(value, BaseMessage):
            return value.content

        if isinstance(value, Document):
            return value.page_content

        # Handle Pydantic models
        if hasattr(value, "model_dump") and callable(value.model_dump) and not isinstance(value, type):
            try:
                return self._convert_to_openlayer_type(value.model_dump())
            except Exception:  # noqa: BLE001, S110
                pass

        # Handle LangChain tools
        if hasattr(value, "name") and hasattr(value, "description"):
            try:
                return {
                    "name": str(value.name),
                    "description": str(value.description) if value.description else None,
                }
            except Exception:  # noqa: BLE001, S110
                pass

        # Fallback to string for all other types (including generators, None, etc.)
        try:
            return str(value)
        except Exception:  # noqa: BLE001
            return None