def test_load_from_new_style_toml(default_config, temp_toml_file):
    # Test loading configuration from a new-style TOML file
    with open(temp_toml_file, 'w', encoding='utf-8') as toml_file:
        toml_file.write(
            """
[llm]
model = "test-model"
api_key = "toml-api-key"

[llm.cheap]
model = "some-cheap-model"
api_key = "cheap-model-api-key"

[agent]
enable_prompt_extensions = true

[agent.BrowsingAgent]
llm_config = "cheap"
enable_prompt_extensions = false

[sandbox]
timeout = 1
volumes = "/opt/files2/workspace:/workspace:rw"

[core]
default_agent = "TestAgent"
"""
        )

    load_from_toml(default_config, temp_toml_file)

    # default llm & agent configs
    assert default_config.default_agent == 'TestAgent'
    assert default_config.get_llm_config().model == 'test-model'
    assert default_config.get_llm_config().api_key.get_secret_value() == 'toml-api-key'
    assert default_config.get_agent_config().enable_prompt_extensions is True

    # undefined agent config inherits default ones
    assert (
        default_config.get_llm_config_from_agent('CodeActAgent')
        == default_config.get_llm_config()
    )
    assert (
        default_config.get_agent_config('CodeActAgent').enable_prompt_extensions is True
    )

    # defined agent config overrides default ones
    assert default_config.get_llm_config_from_agent(
        'BrowsingAgent'
    ) == default_config.get_llm_config('cheap')
    assert (
        default_config.get_llm_config_from_agent('BrowsingAgent').model
        == 'some-cheap-model'
    )
    assert (
        default_config.get_agent_config('BrowsingAgent').enable_prompt_extensions
        is False
    )

    assert default_config.sandbox.volumes == '/opt/files2/workspace:/workspace:rw'
    assert default_config.sandbox.timeout == 1

    assert default_config.workspace_mount_path is None
    assert default_config.workspace_mount_path_in_sandbox is not None
    assert default_config.workspace_mount_path_in_sandbox == '/workspace'

    finalize_config(default_config)

    # after finalize_config, workspace_mount_path is set based on sandbox.volumes
    assert default_config.workspace_mount_path == os.path.abspath(
        '/opt/files2/workspace'
    )
    assert default_config.workspace_mount_path_in_sandbox == '/workspace'