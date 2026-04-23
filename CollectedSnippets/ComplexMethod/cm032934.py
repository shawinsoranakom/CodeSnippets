def _is_metadata_list(obj: list) -> bool:
    if not isinstance(obj, list) or not obj:
        return False
    for item in obj:
        if not isinstance(item, dict):
            return False
        key = item.get("key")
        if not isinstance(key, str) or not key:
            return False
        if "enum" in item and not isinstance(item["enum"], list):
            return False
        if "description" in item and not isinstance(item["description"], str):
            return False
        if "descriptions" in item and not isinstance(item["descriptions"], str):
            return False
    return True