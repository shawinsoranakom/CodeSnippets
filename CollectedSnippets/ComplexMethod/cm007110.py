def _extract_content_for_upload(self) -> str:
        """Extract content from input for upload to cloud services."""
        if self._get_input_type() == "DataFrame":
            return self.input.to_csv(index=False)
        if self._get_input_type() == "Data":
            if hasattr(self.input, "data") and self.input.data:
                if isinstance(self.input.data, dict):
                    import json

                    return json.dumps(self.input.data, indent=2, ensure_ascii=False)
                return str(self.input.data)
            return str(self.input)
        if self._get_input_type() == "Message":
            return str(self.input.text) if self.input.text else str(self.input)
        return str(self.input)