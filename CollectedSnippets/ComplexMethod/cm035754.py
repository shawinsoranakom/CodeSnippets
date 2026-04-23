async def test_mcp_settings_merge_both_present():
    """Test merging when both config.toml and frontend have MCP settings."""
    mock_config_settings = _settings_with_mcp(
        MCPConfig(
            mcpServers={
                'config-sse': RemoteMCPServer(
                    url='http://config-server.com', transport='sse'
                ),
                'config-stdio': StdioMCPServer(command='config-cmd', args=['arg1']),
            }
        )
    )

    frontend_settings = _settings_with_mcp(
        MCPConfig(
            mcpServers={
                'frontend-sse': RemoteMCPServer(
                    url='http://frontend-server.com', transport='sse'
                ),
                'frontend-stdio': StdioMCPServer(command='frontend-cmd', args=['arg2']),
            }
        ),
        llm=LLM(model='gpt-4'),
    )

    with patch(
        'openhands.storage.data_models.settings.Settings.from_config',
        return_value=mock_config_settings,
    ):
        merged_settings = frontend_settings.merge_with_config_settings()

    merged_mcp_config = _mcp_config(merged_settings)
    assert merged_mcp_config is not None
    assert len(merged_mcp_config.mcpServers) == 4
    assert 'config-sse' in merged_mcp_config.mcpServers
    assert 'frontend-sse' in merged_mcp_config.mcpServers
    assert 'config-stdio' in merged_mcp_config.mcpServers
    assert 'frontend-stdio' in merged_mcp_config.mcpServers
    assert merged_settings.agent_settings.llm.model == 'gpt-4'