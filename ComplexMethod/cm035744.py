def test_env_overrides_sandbox_toml(monkeypatch, default_config, temp_toml_file):
    # test that environment variables override TOML values using monkeypatch
    # uses a toml file with a sandbox section
    with open(temp_toml_file, 'w', encoding='utf-8') as toml_file:
        toml_file.write("""
[llm]
model = "test-model"
api_key = "toml-api-key"

[core]

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

    # before load_from_env, values are set to the values from the toml file
    assert default_config.get_llm_config().api_key.get_secret_value() == 'toml-api-key'
    assert default_config.sandbox.volumes == '/opt/files3/workspace:/workspace:rw'
    assert default_config.sandbox.timeout == 500
    assert default_config.sandbox.user_id == 1001

    load_from_env(default_config, os.environ)

    # values from env override values from toml
    assert os.environ.get('LLM_MODEL') is None
    assert default_config.get_llm_config().model == 'test-model'
    assert default_config.get_llm_config().api_key.get_secret_value() == 'env-api-key'
    assert default_config.sandbox.volumes == '/tmp/test:/workspace:ro'
    assert default_config.sandbox.timeout == 1000
    assert default_config.sandbox.user_id == 1002

    finalize_config(default_config)
    # after finalize_config, workspace_mount_path is set based on sandbox.volumes
    assert default_config.workspace_mount_path == os.path.abspath('/tmp/test')
    assert default_config.workspace_mount_path_in_sandbox == '/workspace'