def convert_request_kwargs(parameters: dict, input_shape: StructureShape) -> dict:
    """
    Transform a dict of request kwargs for a boto3 request by making sure the keys in the structure recursively conform to the specified input shape.
    :param parameters: the kwargs that would be passed to the boto3 client call, e.g. boto3.client("s3").create_bucket(**parameters)
    :param input_shape: The botocore input shape of the operation that you want to call later with the fixed inputs
    :return: a transformed dictionary with the correct casing recursively applied
    """

    def get_fixed_key(key: str, members: dict[str, Shape]) -> str:
        """return the case-insensitively matched key from the shape or default to the current key"""
        for k in members:
            if k.lower() == key.lower():
                return k
        return key

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

    transformed_dict = {}
    for key, value in parameters.items():
        correct_key = get_fixed_key(key, input_shape.members)
        member_shape = input_shape.members.get(correct_key)

        if member_shape is None:
            continue  # skipping this entry, so it's not included in the transformed dict
        elif isinstance(value, dict) and hasattr(member_shape, "members"):
            transformed_dict[correct_key] = convert_request_kwargs(value, member_shape)
        elif isinstance(value, list) and hasattr(member_shape, "member"):
            transformed_dict[correct_key] = [
                transform_value(item, member_shape.member) for item in value
            ]
        else:
            transformed_dict[correct_key] = transform_value(value, member_shape)

    return transformed_dict