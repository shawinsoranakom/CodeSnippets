def transform_value(value, member_shape):
        if isinstance(value, dict) and hasattr(member_shape, "members"):
            return convert_request_kwargs(value, member_shape)
        elif isinstance(value, list) and hasattr(member_shape, "member"):
            return [transform_value(item, member_shape.member) for item in value]

        # fix the typing of the value
        match member_shape.type_name:
            case "string":
                return str(value)
            case "integer" | "long":
                return int(value)
            case "boolean":
                if isinstance(value, bool):
                    return value
                return True if value.lower() == "true" else False
            case _:
                return value