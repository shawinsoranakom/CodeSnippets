def extract_friendly_error(error_msg: str) -> str:
    """Convert technical API errors into user-friendly messages."""
    error_lower = error_msg.lower()

    # Pydantic schema validation errors — checked BEFORE the generic pattern loop
    # so a message like "HTTPException 500: 1 validation error for InputSchema..."
    # is not masked by the "500" → "Server error" fallback.
    schema_error_terms = ("validation error for", "input should be a valid", "pydantic.validationerror")
    if any(term in error_lower for term in schema_error_terms):
        return (
            "The selected model produced output that didn't match the expected schema. "
            "Try again or use a more capable model."
        )

    for patterns, friendly_message in ERROR_PATTERNS:
        if any(pattern in error_lower or pattern in error_msg for pattern in patterns):
            return friendly_message

    model_missing_terms = ("not found", "does not exist", "not available")
    if "model" in error_lower and any(term in error_lower for term in model_missing_terms):
        return "Model not available. Please select a different model."

    if "content" in error_lower and any(term in error_lower for term in ["filter", "policy", "safety"]):
        return "Request blocked by content policy. Please modify your prompt."

    return _truncate_error_message(error_msg)