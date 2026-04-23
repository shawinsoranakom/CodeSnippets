def test_sandbox_config_from_toml(monkeypatch, default_config, temp_toml_file):
    # Test loading configuration from a new-style TOML file
    with open(temp_toml_file, 'w', encoding='utf-8') as toml_file:
        toml_file.write(
            """
[core]

[llm]
model = "test-model"

[sandbox]
volumes = "/opt/files/workspace:/workspace:rw"
timeout = 1
base_container_image = "custom_image"
user_id = 1001
"""
        )
    monkeypatch.setattr(os, 'environ', {})
    load_from_toml(default_config, temp_toml_file)
    load_from_env(default_config, os.environ)
    finalize_config(default_config)

    assert default_config.get_llm_config().model == 'test-model'
    assert default_config.sandbox.volumes == '/opt/files/workspace:/workspace:rw'
    assert default_config.workspace_mount_path == os.path.abspath(
        '/opt/files/workspace'
    )
    assert default_config.workspace_mount_path_in_sandbox == '/workspace'
    assert default_config.sandbox.timeout == 1
    assert default_config.sandbox.base_container_image == 'custom_image'
    assert default_config.sandbox.user_id == 1001