async def call_tool_mcp(mcp_clients: list[MCPClient], action: MCPAction) -> Observation:
    """Call a tool on an MCP server and return the observation.

    Args:
        mcp_clients: The list of MCP clients to execute the action on
        action: The MCP action to execute

    Returns:
        The observation from the MCP server
    """
    import sys

    from openhands.events.observation import ErrorObservation

    # Skip MCP tools on Windows
    if sys.platform == 'win32':
        logger.info('MCP functionality is disabled on Windows')
        return ErrorObservation('MCP functionality is not available on Windows')

    if not mcp_clients:
        raise ValueError('No MCP clients found')

    logger.debug(f'MCP action received: {action}')

    # Find the MCP client that has the matching tool name
    matching_client = None
    logger.debug(f'MCP clients: {mcp_clients}')
    logger.debug(f'MCP action name: {action.name}')

    for client in mcp_clients:
        logger.debug(f'MCP client tools: {client.tools}')
        if action.name in [tool.name for tool in client.tools]:
            matching_client = client
            break

    if matching_client is None:
        raise ValueError(f'No matching MCP agent found for tool name: {action.name}')

    logger.debug(f'Matching client: {matching_client}')

    try:
        # Call the tool - this will create a new connection internally
        response = await matching_client.call_tool(action.name, action.arguments)
        logger.debug(f'MCP response: {response}')

        return MCPObservation(
            content=json.dumps(response.model_dump(mode='json')),
            name=action.name,
            arguments=action.arguments,
        )
    except asyncio.TimeoutError:
        # Handle timeout errors specifically
        timeout_val = getattr(matching_client, 'server_timeout', 'unknown')
        logger.error(f'MCP tool {action.name} timed out after {timeout_val}s')
        error_content = json.dumps(
            {
                'isError': True,
                'error': f'Tool "{action.name}" timed out after {timeout_val} seconds',
                'content': [],
            }
        )
        return MCPObservation(
            content=error_content,
            name=action.name,
            arguments=action.arguments,
        )
    except McpError as e:
        # Handle MCP errors by returning an error observation instead of raising
        logger.error(f'MCP error when calling tool {action.name}: {e}')
        error_content = json.dumps({'isError': True, 'error': str(e), 'content': []})
        return MCPObservation(
            content=error_content,
            name=action.name,
            arguments=action.arguments,
        )