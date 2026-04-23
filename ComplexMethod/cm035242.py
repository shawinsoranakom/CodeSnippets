async def _get_agent_server_context(
    conversation_id: UUID,
    app_conversation_service: AppConversationService,
    sandbox_service: SandboxService,
    sandbox_spec_service: SandboxSpecService,
) -> AgentServerContext | JSONResponse | None:
    """Get the agent server context for a conversation.

    This helper retrieves all necessary information to communicate with the
    agent server for a given conversation, including the sandbox info,
    sandbox spec, and agent server URL.

    Args:
        conversation_id: The conversation ID
        app_conversation_service: Service for conversation operations
        sandbox_service: Service for sandbox operations
        sandbox_spec_service: Service for sandbox spec operations

    Returns:
        AgentServerContext if successful, JSONResponse(404) if conversation
        not found, or None if sandbox is not running (e.g. closed conversation).
    """
    # Get the conversation info
    conversation = await app_conversation_service.get_app_conversation(conversation_id)
    if not conversation:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'error': f'Conversation {conversation_id} not found'},
        )

    # Get the sandbox info
    sandbox = await sandbox_service.get_sandbox(conversation.sandbox_id)
    if not sandbox:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'error': f'Sandbox not found for conversation {conversation_id}'},
        )
    # Return None for paused sandboxes (closed conversation)
    if sandbox.status == SandboxStatus.PAUSED:
        return None
    # Return 404 for other non-running states (STARTING, ERROR, MISSING)
    if sandbox.status != SandboxStatus.RUNNING:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'error': f'Sandbox not ready for conversation {conversation_id}'},
        )

    # Get the sandbox spec to find the working directory
    sandbox_spec = await sandbox_spec_service.get_sandbox_spec(sandbox.sandbox_spec_id)
    if not sandbox_spec:
        # TODO: This is a temporary work around for the fact that we don't store previous
        # sandbox spec versions when updating OpenHands. When the SandboxSpecServices
        # transition to truly multi sandbox spec model this should raise a 404 error
        logger.warning('Sandbox spec not found - using default.')
        sandbox_spec = await sandbox_spec_service.get_default_sandbox_spec()

    # Get the agent server URL
    if not sandbox.exposed_urls:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'error': 'No agent server URL found for sandbox'},
        )

    agent_server_url = None
    for exposed_url in sandbox.exposed_urls:
        if exposed_url.name == AGENT_SERVER:
            agent_server_url = exposed_url.url
            break

    if not agent_server_url:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'error': 'Agent server URL not found in sandbox'},
        )

    agent_server_url = replace_localhost_hostname_for_docker(agent_server_url)

    return AgentServerContext(
        conversation=conversation,
        sandbox=sandbox,
        sandbox_spec=sandbox_spec,
        agent_server_url=agent_server_url,
        session_api_key=sandbox.session_api_key,
    )