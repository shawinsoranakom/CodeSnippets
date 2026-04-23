async def create_mcp_clients(
    mcp_config: MCPConfig,
    conversation_id: str | None = None,
) -> list[MCPClient]:
    """Create MCP clients from an MCPConfig.

    Args:
        mcp_config: Unified MCP configuration.
        conversation_id: Optional conversation ID for remote servers.
    """
    import sys

    if sys.platform == 'win32':
        logger.info(
            'MCP functionality is disabled on Windows, skipping client creation'
        )
        return []

    if not mcp_config.mcpServers:
        return []

    mcp_clients: list[MCPClient] = []

    for name, server in mcp_config.mcpServers.items():
        if isinstance(server, StdioMCPServer):
            if not shutil.which(server.command):
                logger.error(
                    f'Skipping MCP stdio server "{name}": command "{server.command}" not found. '
                    f'Please install {server.command} or remove this server from your configuration.'
                )
                continue

            logger.info(
                f'Initializing MCP agent for {redact_text_secrets(str(server))} with stdio connection...'
            )
            client = MCPClient()
            try:
                await client.connect_stdio(server, name=name)
                tool_names = [tool.name for tool in client.tools]
                logger.debug(
                    f'Successfully connected to MCP stdio server {name} - '
                    f'provides {len(tool_names)} tools: {tool_names}'
                )
                mcp_clients.append(client)
            except Exception as e:
                logger.error(
                    f'Failed to connect to {redact_text_secrets(str(server))}: {str(e)}',
                    exc_info=True,
                )
            continue

        if isinstance(server, RemoteMCPServer):
            transport = server.transport or 'http'
            logger.info(
                f'Initializing MCP agent for {redact_text_secrets(str(server))} with {transport} connection...'
            )
            client = MCPClient()

            if server.timeout is not None:
                client.server_timeout = float(server.timeout)
                logger.debug(f'Set server timeout to {server.timeout}s')

            try:
                await client.connect_http(server, conversation_id=conversation_id)
                tool_names = [tool.name for tool in client.tools]
                logger.debug(
                    f'Successfully connected to MCP server {redact_url_params(server.url)} - '
                    f'provides {len(tool_names)} tools: {tool_names}'
                )
                mcp_clients.append(client)
            except Exception as e:
                logger.error(
                    f'Failed to connect to {redact_text_secrets(str(server))}: {str(e)}',
                    exc_info=True,
                )

    return mcp_clients