def test_env_overrides_compat_toml(monkeypatch, default_config, temp_toml_file):
    # test that environment variables override TOML values using monkeypatch
    # uses a toml file with sandbox_vars instead of a sandbox section
    with open(temp_toml_file, 'w', encoding='utf-8') as toml_file:
        toml_file.write("""
[llm]
model = "test-model"
api_key = "toml-api-key"

[core]
disable_color = true

[sandbox]
volumes = "/opt/files3/workspace:/workspace:rw"
timeout = 500
user_id = 1001
""")

    monkeypatch.setenv('LLM_API_KEY', 'env-api-key')
    monkeypatch.setenv('SANDBOX_VOLUMES', '/tmp/test:/workspace:ro')
    monkeypatch.setenv('SANDBOX_TIMEOUT', '1000')
    monkeypatch.setenv('SANDBOX_USER_ID', '1002')
    monkeypatch.delenv('LLM_MODEL', raising=False)

    load_from_toml(default_config, temp_toml_file)

    assert default_config.workspace_mount_path is None

    load_from_env(default_config, os.environ)

    assert os.environ.get('LLM_MODEL') is None
    assert default_config.get_llm_config().model == 'test-model'
    assert default_config.get_llm_config('llm').model == 'test-model'
    assert default_config.get_llm_config_from_agent().model == 'test-model'
    assert default_config.get_llm_config().api_key.get_secret_value() == 'env-api-key'

    # Environment variable should override TOML value
    assert default_config.sandbox.volumes == '/tmp/test:/workspace:ro'
    assert default_config.workspace_mount_path is None

    assert default_config.disable_color is True
    assert default_config.sandbox.timeout == 1000
    assert default_config.sandbox.user_id == 1002

    finalize_config(default_config)
    # after finalize_config, workspace_mount_path is set based on the sandbox.volumes
    assert default_config.workspace_mount_path == os.path.abspath('/tmp/test')
    assert default_config.workspace_mount_path_in_sandbox == '/workspace'