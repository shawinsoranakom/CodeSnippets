def test_compat_env_to_config(monkeypatch, setup_env):
    # Use `monkeypatch` to set environment variables for this specific test
    monkeypatch.setenv('SANDBOX_VOLUMES', '/repos/openhands/workspace:/workspace:rw')
    monkeypatch.setenv('LLM_API_KEY', 'sk-proj-rgMV0...')
    monkeypatch.setenv('LLM_MODEL', 'gpt-4o')
    monkeypatch.setenv('DEFAULT_AGENT', 'CodeActAgent')
    monkeypatch.setenv('SANDBOX_TIMEOUT', '10')

    config = OpenHandsConfig()
    load_from_env(config, os.environ)
    finalize_config(config)

    assert config.sandbox.volumes == '/repos/openhands/workspace:/workspace:rw'
    # Check that the old parameters are set for backward compatibility
    assert config.workspace_base == os.path.abspath('/repos/openhands/workspace')
    assert config.workspace_mount_path == os.path.abspath('/repos/openhands/workspace')
    assert config.workspace_mount_path_in_sandbox == '/workspace'
    assert isinstance(config.get_llm_config(), LLMConfig)
    assert config.get_llm_config().api_key.get_secret_value() == 'sk-proj-rgMV0...'
    assert config.get_llm_config().model == 'gpt-4o'
    assert isinstance(config.get_agent_config(), AgentConfig)
    assert config.default_agent == 'CodeActAgent'
    assert config.sandbox.timeout == 10