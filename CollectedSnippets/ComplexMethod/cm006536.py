async def verify_public_flow_and_get_user(
    flow_id: uuid.UUID,
    client_id: str | None,
    authenticated_user_id: uuid.UUID | None = None,
) -> tuple[User, uuid.UUID]:
    """Verify a public flow request and generate a deterministic flow ID.

    This utility function:
    1. Checks that a client_id cookie or authenticated_user_id is provided
    2. Verifies the flow exists and is marked as PUBLIC
    3. Creates a deterministic UUID based on the identifier and original flow_id
    4. Retrieves the flow owner user for permission purposes

    When an authenticated_user_id is provided, it takes precedence over client_id
    for UUID v5 generation. This enables DB-persisted sessions for logged-in users
    on the shareable playground.

    Args:
        flow_id: The original flow ID to verify
        client_id: The client ID from the request cookie
        authenticated_user_id: The authenticated user's ID (takes precedence over client_id)

    Returns:
        tuple: (flow owner user, deterministic flow ID for tracking)

    Raises:
        HTTPException:
            - 400 if neither client_id nor authenticated_user_id is provided
            - 403 if flow doesn't exist or isn't public
            - 403 if unable to retrieve the flow owner user
            - 403 if user is not found for public flow
    """
    if not client_id and not authenticated_user_id:
        raise HTTPException(status_code=400, detail="No client_id cookie found")

    # Check if the flow is public
    async with session_scope() as session:
        from sqlmodel import select

        from langflow.services.database.models.flow.model import AccessTypeEnum, Flow

        flow = (await session.exec(select(Flow).where(Flow.id == flow_id))).first()
        if not flow or flow.access_type is not AccessTypeEnum.PUBLIC:
            raise HTTPException(status_code=403, detail="Flow is not public")

    # Use authenticated user_id for deterministic UUID when available, otherwise client_id
    identifier = str(authenticated_user_id) if authenticated_user_id else client_id
    new_flow_id = compute_virtual_flow_id(identifier, flow_id)

    # Get the user associated with the flow
    try:
        from langflow.helpers.user import get_user_by_flow_id_or_endpoint_name

        user = await get_user_by_flow_id_or_endpoint_name(str(flow_id))

    except Exception as exc:
        await logger.aexception("Error getting user for public flow %s", flow_id)
        raise HTTPException(status_code=403, detail="Flow is not accessible") from exc

    if not user:
        raise HTTPException(status_code=403, detail="Flow is not accessible")

    return user, new_flow_id