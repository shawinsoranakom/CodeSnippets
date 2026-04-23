def validate_safejson_type(obj):
            """Ensure object only contains SafeJson compatible types."""
            if obj is None:
                return True
            elif isinstance(obj, (str, int, float, bool)):
                return True
            elif isinstance(obj, dict):
                return all(
                    isinstance(k, str) and validate_safejson_type(v)
                    for k, v in obj.items()
                )
            elif isinstance(obj, list):
                return all(validate_safejson_type(item) for item in obj)
            else:
                return False