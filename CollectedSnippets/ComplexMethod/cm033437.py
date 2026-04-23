def validate_and_parse_request_args(request: Request, validator: type[BaseModel], *, extras: dict[str, Any] | None = None) -> tuple[dict[str, Any] | None, str | None]:
    """
    Validates and parses request arguments against a Pydantic model.

    This function performs a complete request validation workflow:
    1. Extracts query parameters from the request
    2. Merges with optional extra values (if provided)
    3. Validates against the specified Pydantic model
    4. Cleans the output by removing extra values
    5. Returns either parsed data or an error message

    Args:
        request (Request): Web framework request object containing query parameters
        validator (type[BaseModel]): Pydantic model class for validation
        extras (dict[str, Any] | None): Optional additional values to include in validation
                                      but exclude from final output. Defaults to None.

    Returns:
        tuple[dict[str, Any] | None, str | None]:
            - First element: Validated/parsed arguments as dict if successful, None otherwise
            - Second element: Formatted error message if validation failed, None otherwise

    Behavior:
        - Query parameters are merged with extras before validation
        - Extras are automatically removed from the final output
        - All validation errors are formatted into a human-readable string

    Raises:
        TypeError: If validator is not a Pydantic BaseModel subclass

    Examples:
        Successful validation:
            >>> validate_and_parse_request_args(request, MyValidator)
            ({'param1': 'value'}, None)

        Failed validation:
            >>> validate_and_parse_request_args(request, MyValidator)
            (None, "param1: Field required")

        With extras:
            >>> validate_and_parse_request_args(request, MyValidator, extras={'internal_id': 123})
            ({'param1': 'value'}, None)  # internal_id removed from output

    Notes:
        - Uses request.args.to_dict() for Flask-compatible parameter extraction
        - Maintains immutability of original request arguments
        - Preserves type conversion from Pydantic validation
    """
    args = request.args.to_dict(flat=True)

    # Handle ext parameter: parse JSON string to dict if it's a string
    if 'ext' in args and isinstance(args['ext'], str):
        import json
        try:
            args['ext'] = json.loads(args['ext'])
        except json.JSONDecodeError:
            pass  # Keep the string and let validation handle the error

    try:
        if extras is not None:
            args.update(extras)
        validated_args = validator(**args)
    except ValidationError as e:
        return None, format_validation_error_message(e)

    parsed_args = validated_args.model_dump()
    if extras is not None:
        for key in list(parsed_args.keys()):
            if key in extras:
                del parsed_args[key]

    return parsed_args, None