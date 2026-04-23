def test_create_user_settings_from_entities_with_org_fallback():
    """Test that _create_user_settings_from_entities falls back to org defaults."""
    user_id = str(uuid.uuid4())

    # Create mock entities with None in OrgMember
    org_member = MagicMock()
    org_member.llm_api_key = None
    org_member.agent_settings_diff = {}
    org_member.conversation_settings_diff = {}

    user = MagicMock()
    user.accepted_tos = None
    user.enable_sound_notifications = False
    user.language = 'es'
    user.user_consents_to_analytics = False
    user.email = None
    user.email_verified = None
    user.git_user_name = None
    user.git_user_email = None

    org = MagicMock()
    org.remote_runtime_resource_factor = 2.0
    org.billing_margin = 0.1
    org.enable_proactive_conversation_starters = False
    org.sandbox_base_container_image = 'custom-image'
    org.sandbox_runtime_container_image = None
    org.org_version = 2
    org.agent_settings = {
        'agent': 'CodeActAgent',
        'llm': {
            'model': 'default-model',
            'base_url': 'https://default.api.com',
        },
        'condenser': {
            'enabled': False,
            'max_size': 1000,
        },
    }
    org.conversation_settings = {
        'confirmation_mode': True,
        'max_iterations': 100,
    }
    org.search_api_key = SecretStr('search-key')
    org.sandbox_api_key = None
    org.max_budget_per_task = 10.0
    org.enable_solvability_analysis = True
    org.v1_enabled = False

    result = UserStore._create_user_settings_from_entities(
        user_id, org_member, user, org
    )

    # Should have fallen back to org defaults
    assert result.agent_settings['llm']['model'] == 'default-model'
    assert result.agent_settings['llm']['base_url'] == 'https://default.api.com'
    assert result.agent_settings['agent'] == 'CodeActAgent'
    assert result.agent_settings['condenser']['max_size'] == 1000
    assert result.conversation_settings['confirmation_mode'] is True
    assert result.conversation_settings['max_iterations'] == 100
    assert result.language == 'es'
    assert result.search_api_key == 'search-key'