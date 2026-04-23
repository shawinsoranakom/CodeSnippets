def _values_equal(
        self, 
        field_name: str, 
        es_value: Any, 
        ob_value: Any
    ) -> bool:
        """Compare two values with type-aware logic."""
        if es_value is None and ob_value is None:
            return True

        if es_value is None or ob_value is None:
            # One is None, the other isn't
            # For optional fields, this might be acceptable
            return False

        # Handle array fields (stored as JSON strings in OB)
        if field_name in ARRAY_COLUMNS:
            if isinstance(ob_value, str):
                try:
                    ob_value = json.loads(ob_value)
                except json.JSONDecodeError:
                    pass
            if isinstance(es_value, list) and isinstance(ob_value, list):
                return set(str(x) for x in es_value) == set(str(x) for x in ob_value)

        # Handle JSON fields
        if field_name in JSON_COLUMNS:
            if isinstance(ob_value, str):
                try:
                    ob_value = json.loads(ob_value)
                except json.JSONDecodeError:
                    pass
            if isinstance(es_value, str):
                try:
                    es_value = json.loads(es_value)
                except json.JSONDecodeError:
                    pass
            return es_value == ob_value

        # Handle content_with_weight which might be dict or string
        if field_name == "content_with_weight":
            if isinstance(ob_value, str) and isinstance(es_value, dict):
                try:
                    ob_value = json.loads(ob_value)
                except json.JSONDecodeError:
                    pass

        # Handle kb_id which might be list in ES
        if field_name == "kb_id":
            if isinstance(es_value, list) and len(es_value) > 0:
                es_value = es_value[0]

        # Standard comparison
        return str(es_value) == str(ob_value)