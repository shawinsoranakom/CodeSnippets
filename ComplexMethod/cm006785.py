def parse_google_service_account_key(service_account_key: str) -> dict:
    """Parse Google service account JSON key with multiple fallback strategies.

    This function handles various common formatting issues when users paste
    service account keys, including:
    - Control characters
    - Extra whitespace
    - Double-encoded JSON strings
    - Escaped newlines in private_key field

    Args:
        service_account_key: Service account JSON key as string

    Returns:
        dict: Parsed service account credentials

    Raises:
        ValueError: If all parsing strategies fail
    """
    credentials_dict = None
    parse_errors = []

    # Strategy 1: Parse as-is with strict=False to allow control characters
    try:
        credentials_dict = json.loads(service_account_key, strict=False)
    except json.JSONDecodeError as e:
        parse_errors.append(f"Standard parse: {e!s}")

    # Strategy 2: Strip whitespace and try again
    if credentials_dict is None:
        try:
            cleaned_key = service_account_key.strip()
            credentials_dict = json.loads(cleaned_key, strict=False)
        except json.JSONDecodeError as e:
            parse_errors.append(f"Stripped parse: {e!s}")

    # Strategy 3: Check if it's double-encoded (JSON string of a JSON string)
    if credentials_dict is None:
        try:
            decoded_once = json.loads(service_account_key, strict=False)
            credentials_dict = json.loads(decoded_once, strict=False) if isinstance(decoded_once, str) else decoded_once
        except json.JSONDecodeError as e:
            parse_errors.append(f"Double-encoded parse: {e!s}")

    # Strategy 4: Try to fix common issues with newlines in the private_key field
    if credentials_dict is None:
        try:
            # Replace literal \n with actual newlines which is common in pasted JSON
            fixed_key = service_account_key.replace("\\n", "\n")
            credentials_dict = json.loads(fixed_key, strict=False)
        except json.JSONDecodeError as e:
            parse_errors.append(f"Newline-fixed parse: {e!s}")

    if credentials_dict is None:
        error_details = "; ".join(parse_errors)
        msg = (
            f"Unable to parse service account key JSON. Tried multiple strategies: {error_details}. "
            "Please ensure you've copied the entire JSON content from your service account key file. "
            "The JSON should start with '{' and contain fields like 'type', 'project_id', 'private_key', etc."
        )
        raise ValueError(msg)

    return credentials_dict