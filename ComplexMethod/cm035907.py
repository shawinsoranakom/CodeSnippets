def test_create_user_settings_from_entities():
    """Test creating UserSettings from OrgMember, User, and Org entities."""
    user_id = str(uuid.uuid4())

    # Create mock entities
    org_member = MagicMock()
    org_member.llm_api_key = SecretStr('test-api-key')
    org_member.agent_settings_diff = {
        'llm': {
            'model': 'claude-3-5-sonnet',
            'base_url': 'https://api.example.com',
        },
    }
    org_member.conversation_settings_diff = {
        'max_iterations': 50,
    }

    user = MagicMock()
    user.accepted_tos = None
    user.enable_sound_notifications = True
    user.language = 'en'
    user.user_consents_to_analytics = True
    user.email = 'test@example.com'
    user.email_verified = True
    user.git_user_name = 'testuser'
    user.git_user_email = 'test@git.com'

    org = MagicMock()
    org.remote_runtime_resource_factor = 1.0
    org.billing_margin = 0.0
    org.enable_proactive_conversation_starters = True
    org.sandbox_base_container_image = None
    org.sandbox_runtime_container_image = None
    org.org_version = 1
    org.agent_settings = {
        'agent': 'CodeActAgent',
    }
    org.conversation_settings = {
        'security_analyzer': 'llm',
    }
    org.search_api_key = None
    org.sandbox_api_key = None
    org.max_budget_per_task = None
    org.enable_solvability_analysis = False
    org.v1_enabled = True

    result = UserStore._create_user_settings_from_entities(
        user_id, org_member, user, org
    )

    assert result.keycloak_user_id == user_id
    assert result.llm_api_key == 'test-api-key'
    assert result.agent_settings['llm']['model'] == 'claude-3-5-sonnet'
    assert result.agent_settings['llm']['base_url'] == 'https://api.example.com'
    assert result.agent_settings['agent'] == 'CodeActAgent'
    assert result.conversation_settings['security_analyzer'] == 'llm'
    assert result.conversation_settings['max_iterations'] == 50
    assert result.language == 'en'
    assert result.email == 'test@example.com'