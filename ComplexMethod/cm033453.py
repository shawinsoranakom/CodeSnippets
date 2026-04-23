def _convert_field_value(
        self, 
        field_name: str, 
        value: Any, 
        field_def: dict[str, Any]
    ) -> Any:
        """
        Convert a field value to the appropriate format for OceanBase.

        Args:
            field_name: Field name
            value: Original value from ES
            field_def: Field definition from RAGFLOW_COLUMNS

        Returns:
            Converted value
        """
        if value is None:
            return None

        ob_type = field_def.get("ob_type", "")
        is_array = field_def.get("is_array", False)
        is_json = field_def.get("is_json", False)

        # Handle array fields
        if is_array:
            return self._convert_array_value(value)

        # Handle JSON fields
        if is_json:
            return self._convert_json_value(value)

        # Handle specific types
        if "Integer" in ob_type:
            return self._convert_integer(value)

        if "Double" in ob_type or "Float" in ob_type:
            return self._convert_float(value)

        if "LONGTEXT" in ob_type or "TEXT" in ob_type:
            return self._convert_text(value)

        if "String" in ob_type:
            return self._convert_string(value, field_name)

        # Default: convert to string
        return str(value) if value is not None else None