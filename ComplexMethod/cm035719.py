async def test_get_env_vars():
    """Test get_env_vars with different configurations"""
    tokens = MappingProxyType(
        {
            ProviderType.GITHUB: ProviderToken(token=SecretStr('test_token')),
            ProviderType.GITLAB: ProviderToken(token=SecretStr('gitlab_token')),
        }
    )
    handler = ProviderHandler(provider_tokens=tokens)

    # Test getting all tokens unexposed
    env_vars = await handler.get_env_vars(expose_secrets=False)
    assert isinstance(env_vars, dict)
    assert isinstance(env_vars[ProviderType.GITHUB], SecretStr)
    assert env_vars[ProviderType.GITHUB].get_secret_value() == 'test_token'
    assert env_vars[ProviderType.GITLAB].get_secret_value() == 'gitlab_token'

    # Test getting specific providers
    env_vars = await handler.get_env_vars(
        expose_secrets=False, providers=[ProviderType.GITHUB]
    )
    assert len(env_vars) == 1
    assert ProviderType.GITHUB in env_vars
    assert ProviderType.GITLAB not in env_vars

    # Test exposed secrets
    exposed_vars = await handler.get_env_vars(expose_secrets=True)
    assert isinstance(exposed_vars, dict)
    assert exposed_vars['github_token'] == 'test_token'
    assert exposed_vars['gitlab_token'] == 'gitlab_token'

    # Test empty tokens
    empty_handler = ProviderHandler(provider_tokens=MappingProxyType({}))
    empty_vars = await empty_handler.get_env_vars()
    assert empty_vars == {}