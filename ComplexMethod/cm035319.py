def _extract_and_validate_params(
    matching_tool: dict, param_matches: Iterable[re.Match], fn_name: str
) -> dict:
    params = {}
    # Parse and validate parameters
    required_params = set()
    if 'parameters' in matching_tool and 'required' in matching_tool['parameters']:
        required_params = set(matching_tool['parameters'].get('required', []))

    allowed_params = set()
    if 'parameters' in matching_tool and 'properties' in matching_tool['parameters']:
        allowed_params = set(matching_tool['parameters']['properties'].keys())

    param_name_to_type = {}
    if 'parameters' in matching_tool and 'properties' in matching_tool['parameters']:
        param_name_to_type = {
            name: val.get('type', 'string')
            for name, val in matching_tool['parameters']['properties'].items()
        }

    # Collect parameters
    found_params = set()
    for param_match in param_matches:
        param_name = param_match.group(1)
        param_value = param_match.group(2)

        # Validate parameter is allowed
        if allowed_params and param_name not in allowed_params:
            raise FunctionCallValidationError(
                f"Parameter '{param_name}' is not allowed for function '{fn_name}'. "
                f'Allowed parameters: {allowed_params}'
            )

        # Validate and convert parameter type
        # supported: string, integer, array
        if param_name in param_name_to_type:
            if param_name_to_type[param_name] == 'integer':
                try:
                    param_value = int(param_value)
                except ValueError:
                    raise FunctionCallValidationError(
                        f"Parameter '{param_name}' is expected to be an integer."
                    )
            elif param_name_to_type[param_name] == 'array':
                try:
                    param_value = json.loads(param_value)
                except json.JSONDecodeError:
                    raise FunctionCallValidationError(
                        f"Parameter '{param_name}' is expected to be an array."
                    )
            else:
                # string
                pass

        # Enum check
        if 'enum' in matching_tool['parameters']['properties'][param_name]:
            if (
                param_value
                not in matching_tool['parameters']['properties'][param_name]['enum']
            ):
                raise FunctionCallValidationError(
                    f"Parameter '{param_name}' is expected to be one of {matching_tool['parameters']['properties'][param_name]['enum']}."
                )

        params[param_name] = param_value
        found_params.add(param_name)

    # Check all required parameters are present
    missing_params = required_params - found_params
    if missing_params:
        raise FunctionCallValidationError(
            f"Missing required parameters for function '{fn_name}': {missing_params}"
        )
    return params