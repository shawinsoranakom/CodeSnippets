def clean_json(self) -> Message:
        try:
            from json_repair import repair_json
        except ImportError as e:
            msg = "Could not import the json_repair package. Please install it with `pip install json_repair`."
            raise ImportError(msg) from e

        """Clean the input JSON string based on provided options and return the cleaned JSON string."""
        json_str = self.json_str
        remove_control_chars = self.remove_control_chars
        normalize_unicode = self.normalize_unicode
        validate_json = self.validate_json

        start = json_str.find("{")
        end = json_str.rfind("}")
        if start == -1 or end == -1:
            msg = "Invalid JSON string: Missing '{' or '}'"
            raise ValueError(msg)
        try:
            json_str = json_str[start : end + 1]

            if remove_control_chars:
                json_str = self._remove_control_characters(json_str)
            if normalize_unicode:
                json_str = self._normalize_unicode(json_str)
            if validate_json:
                json_str = self._validate_json(json_str)

            cleaned_json_str = repair_json(json_str)
            result = str(cleaned_json_str)

            self.status = result
            return Message(text=result)
        except Exception as e:
            msg = f"Error cleaning JSON string: {e}"
            raise ValueError(msg) from e