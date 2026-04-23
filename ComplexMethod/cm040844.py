def extract_json(path: str, data: Any) -> Any:
    input_expr = parse(path)

    matches = input_expr.find(data)
    if not matches:
        if _contains_slice_or_wildcard_array(path):
            return []
        raise NoSuchJsonPathError(json_path=path, data=data)

    if len(matches) > 1 or isinstance(matches[0].path, Index):
        value = [match.value for match in matches]

        # AWS StepFunctions breaks jsonpath specifications and instead
        # unpacks literal singleton array accesses.
        if _is_singleton_array_access(path=path) and len(value) == 1:
            value = value[0]
    else:
        value = matches[0].value

    return value