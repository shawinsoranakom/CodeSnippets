def test_defaults_dict_after_updates(default_config):
    # Test that `defaults_dict` retains initial values after updates.
    initial_defaults = default_config.defaults_dict
    assert initial_defaults['workspace_mount_path']['default'] is None
    assert initial_defaults['default_agent']['default'] == 'CodeActAgent'

    updated_config = OpenHandsConfig()
    updated_config.get_llm_config().api_key = 'updated-api-key'
    updated_config.get_llm_config('llm').api_key = 'updated-api-key'
    updated_config.get_llm_config_from_agent('agent').api_key = 'updated-api-key'
    updated_config.get_llm_config_from_agent(
        'BrowsingAgent'
    ).api_key = 'updated-api-key'
    updated_config.default_agent = 'BrowsingAgent'

    defaults_after_updates = updated_config.defaults_dict
    assert defaults_after_updates['default_agent']['default'] == 'CodeActAgent'
    assert defaults_after_updates['workspace_mount_path']['default'] is None
    assert defaults_after_updates['sandbox']['timeout']['default'] == 120
    assert (
        defaults_after_updates['sandbox']['base_container_image']['default']
        == 'nikolaik/python-nodejs:python3.12-nodejs22-slim'
    )
    assert defaults_after_updates == initial_defaults