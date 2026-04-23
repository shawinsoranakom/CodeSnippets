def test_default_activated_tools():
    import importlib.resources

    # Use importlib.resources to access the config file properly
    # This works both when running from source and from installed package
    try:
        with importlib.resources.as_file(
            importlib.resources.files('openhands').joinpath(
                'runtime', 'mcp', 'config.json'
            )
        ) as config_path:
            assert config_path.exists(), f'MCP config file not found at {config_path}'
            with open(config_path, 'r') as f:
                mcp_config = json.load(f)
    except (FileNotFoundError, ImportError):
        # Fallback to the old method for development environments
        project_root = os.path.dirname(openhands.__file__)
        mcp_config_path = os.path.join(project_root, 'runtime', 'mcp', 'config.json')
        assert os.path.exists(mcp_config_path), (
            f'MCP config file not found at {mcp_config_path}'
        )
        with open(mcp_config_path, 'r') as f:
            mcp_config = json.load(f)

    assert 'mcpServers' in mcp_config
    assert 'default' in mcp_config['mcpServers']
    assert 'tools' in mcp_config
    # no tools are always activated yet
    assert len(mcp_config['tools']) == 0