def _convert_to_traceloop_type(self, value):
        """Recursively converts a value to a Traceloop compatible type."""
        from langchain_core.documents import Document
        from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

        from langflow.schema.message import Message

        try:
            if isinstance(value, dict):
                value = {key: self._convert_to_traceloop_type(val) for key, val in value.items()}

            elif isinstance(value, list):
                value = [self._convert_to_traceloop_type(v) for v in value]

            elif isinstance(value, Message):
                value = value.text

            elif isinstance(value, (BaseMessage | HumanMessage | SystemMessage)):
                value = str(value.content) if value.content is not None else ""

            elif isinstance(value, Document):
                value = value.page_content

            elif isinstance(value, (types.GeneratorType | types.NoneType)):
                value = str(value)

            elif isinstance(value, float) and not math.isfinite(value):
                value = "NaN"

        except (TypeError, ValueError) as e:
            logger.warning(f"Failed to convert value {value!r} to traceloop type: {e}")
            return str(value)
        else:
            return value