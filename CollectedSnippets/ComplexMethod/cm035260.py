def validate_conversation_id(conversation_id: str) -> str:
    """
    Validate conversation ID format and length.

    Args:
        conversation_id: The conversation ID to validate

    Returns:
        The validated conversation ID

    Raises:
        HTTPException: If the conversation ID is invalid
    """
    # Check length - UUID hex is 32 characters, allow some flexibility but not excessive
    if len(conversation_id) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Conversation ID is too long',
        )

    # Check for null bytes and other problematic characters
    if '\x00' in conversation_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Conversation ID contains invalid characters',
        )

    # Check for path traversal attempts
    if '..' in conversation_id or '/' in conversation_id or '\\' in conversation_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Conversation ID contains invalid path characters',
        )

    # Check for control characters and newlines
    if any(ord(c) < 32 for c in conversation_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Conversation ID contains control characters',
        )

    return conversation_id