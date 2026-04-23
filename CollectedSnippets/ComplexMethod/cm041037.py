def recursive_convert(obj):
        if isinstance(obj, dict):
            return {
                key: recursive_convert(value) if key not in keys_to_skip else value
                for key, value in obj.items()
            }
        elif isinstance(obj, list):
            return [recursive_convert(item) for item in obj]
        elif isinstance(obj, str) and obj.isdigit():
            return int(obj)
        else:
            return obj