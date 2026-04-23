def mcp_config_from_toml(data: dict[str, Any]) -> dict[str, MCPConfig]:
    """Parse a ``[mcp]`` TOML section into ``{'mcp': MCPConfig}``.

    Accepts the legacy ``sse_servers`` / ``shttp_servers`` / ``stdio_servers``
    list format and converts to the unified ``mcpServers`` dict.
    """
    servers: dict[str, RemoteMCPServer | StdioMCPServer] = {}

    for entry in data.get('sse_servers', []):
        if isinstance(entry, str):
            entry = {'url': entry}
        name = f'sse_{len([k for k in servers if k.startswith("sse_")])}'
        servers[name] = RemoteMCPServer(
            url=entry['url'],
            transport='sse',
            auth=entry.get('api_key'),
        )

    for entry in data.get('shttp_servers', []):
        if isinstance(entry, str):
            entry = {'url': entry}
        name = f'shttp_{len([k for k in servers if k.startswith("shttp_")])}'
        servers[name] = RemoteMCPServer(
            url=entry['url'],
            transport='http',
            auth=entry.get('api_key'),
            timeout=entry.get('timeout', 60),
        )

    for entry in data.get('stdio_servers', []):
        name = entry.get(
            'name', f'stdio_{len([k for k in servers if k.startswith("stdio_")])}'
        )
        servers[name] = StdioMCPServer(
            command=entry['command'],
            args=_parse_stdio_args(entry.get('args', [])),
            env=_parse_stdio_env(entry.get('env', {})),
        )

    return {'mcp': MCPConfig(mcpServers=servers)}