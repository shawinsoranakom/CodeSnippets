def __convert_dict(value: Any) -> dict:
    if isinstance(value, str):
        try:
            result = json.loads(value)
            if isinstance(result, dict):
                return result
            else:
                return {"value": result}
        except json.JSONDecodeError:
            return {"value": value}  # Fallback conversion
    elif isinstance(value, list):
        return {i: value[i] for i in range(len(value))}
    elif isinstance(value, tuple):
        return {i: value[i] for i in range(len(value))}
    elif isinstance(value, dict):
        return value
    else:
        return {"value": value}