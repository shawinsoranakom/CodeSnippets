async def validate_and_parse_json_request(
    request: Request, validator: type[BaseModel], *, extras: dict[str, Any] | None = None, exclude_unset: bool = False
) -> tuple[dict[str, Any] | None, str | None]:
    """
    Validates and parses JSON requests through a multi-stage validation pipeline.

    Implements a four-stage validation process:
    1. Content-Type verification (must be application/json)
    2. JSON syntax validation
    3. Payload structure type checking
    4. Pydantic model validation with error formatting

    Args:
        request (Request): Flask request object containing HTTP payload
        validator (type[BaseModel]): Pydantic model class for data validation
        extras (dict[str, Any] | None): Additional fields to merge into payload
            before validation. These fields will be removed from the final output
        exclude_unset (bool): Whether to exclude fields that have not been explicitly set

    Returns:
        tuple[Dict[str, Any] | None, str | None]:
        - First element:
            - Validated dictionary on success
            - None on validation failure
        - Second element:
            - None on success
            - Diagnostic error message on failure

    Raises:
        UnsupportedMediaType: When Content-Type header is not application/json
        BadRequest: For structural JSON syntax errors
        ValidationError: When payload violates Pydantic schema rules

    Examples:
        >>> validate_and_parse_json_request(valid_request, DatasetSchema)
        ({"name": "Dataset1", "format": "csv"}, None)

        >>> validate_and_parse_json_request(xml_request, DatasetSchema)
        (None, "Unsupported content type: Expected application/json, got text/xml")

        >>> validate_and_parse_json_request(bad_json_request, DatasetSchema)
        (None, "Malformed JSON syntax: Missing commas/brackets or invalid encoding")

    Notes:
        1. Validation Priority:
            - Content-Type verification precedes JSON parsing
            - Structural validation occurs before schema validation
        2. Extra fields added via `extras` parameter are automatically removed
           from the final output after validation
    """
    if request.mimetype != "application/json":
        return None, f"Unsupported content type: Expected application/json, got {request.content_type}"
    try:
        payload = await request.get_json() or {}
    except UnsupportedMediaType:
        return None, f"Unsupported content type: Expected application/json, got {request.content_type}"
    except BadRequest:
        return None, "Malformed JSON syntax: Missing commas/brackets or invalid encoding"

    if not isinstance(payload, dict):
        return None, f"Invalid request payload: expected object, got {type(payload).__name__}"

    try:
        if extras is not None:
            payload.update(extras)
        validated_request = validator(**payload)
    except ValidationError as e:
        return None, format_validation_error_message(e)

    parsed_payload = validated_request.model_dump(by_alias=True, exclude_unset=exclude_unset)

    if extras is not None:
        for key in list(parsed_payload.keys()):
            if key in extras:
                del parsed_payload[key]

    return parsed_payload, None