def get_column_value(column_name: str, value: Any) -> Any:
    # Check chunk table columns first, then doc_meta table columns
    column_type = column_types.get(column_name) or doc_meta_column_types.get(column_name)
    if column_type:
        if isinstance(column_type, String):
            return str(value)
        elif isinstance(column_type, Integer):
            return int(value)
        elif isinstance(column_type, Double):
            return float(value)
        elif isinstance(column_type, ARRAY) or isinstance(column_type, JSON):
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            else:
                return value
        else:
            raise ValueError(f"Unsupported column type for column '{column_name}': {column_type}")
    elif vector_column_pattern.match(column_name):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        else:
            return value
    elif column_name == "_score":
        return float(value)
    else:
        raise ValueError(f"Unknown column '{column_name}' with value '{value}'.")