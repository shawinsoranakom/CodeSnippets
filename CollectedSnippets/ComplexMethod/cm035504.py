async def add_mcp_tools_to_agent(
    agent: 'Agent', runtime: Runtime, memory: 'Memory'
) -> MCPConfig:
    """Add MCP tools to an agent."""
    import sys

    # Skip MCP tools on Windows
    if sys.platform == 'win32':
        logger.info('MCP functionality is disabled on Windows, skipping MCP tools')
        agent.set_mcp_tools([])
        return

    assert runtime.runtime_initialized, (
        'Runtime must be initialized before adding MCP tools'
    )

    extra_stdio_servers: dict[str, StdioMCPServer] = {}

    # Add microagent MCP tools if available
    microagent_mcp_configs = memory.get_microagent_mcp_tools()
    for mcp_cfg in microagent_mcp_configs:
        for name, server in mcp_cfg.mcpServers.items():
            if isinstance(server, StdioMCPServer):
                if name not in extra_stdio_servers:
                    extra_stdio_servers[name] = server
                    logger.warning(f'Added microagent stdio server: {name}')
            else:
                logger.warning(
                    f'Microagent MCP config contains non-stdio server {name}, not yet supported.'
                )

    # Add the runtime as another MCP server
    updated_mcp_config = runtime.get_mcp_config(extra_stdio_servers or None)

    # Fetch the MCP tools
    mcp_tools = await fetch_mcp_tools_from_config(updated_mcp_config)

    tool_names = [tool['function']['name'] for tool in mcp_tools]
    logger.info(f'Loaded {len(mcp_tools)} MCP tools: {tool_names}')

    # Set the MCP tools on the agent
    agent.set_mcp_tools(mcp_tools)

    return updated_mcp_config