def check_object(obj: dict[str, Any]) -> bool:
        if not isinstance(obj, dict):
            return False

        # patternProperties is not supported by llguidance
        if "patternProperties" in obj:
            return True

        # Recursively check all nested objects and arrays
        for value in obj.values():
            if isinstance(value, dict):
                if check_object(value):
                    return True
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict) and check_object(item):
                        return True

        return False