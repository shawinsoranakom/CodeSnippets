def test_token_conversion():
    """Test token conversion in Secrets.create"""
    # Test with string token
    store1 = Settings(
        secrets_store=Secrets(
            provider_tokens={
                ProviderType.GITHUB: ProviderToken(token=SecretStr('test_token'))
            }
        )
    )

    assert (
        store1.secrets_store.provider_tokens[
            ProviderType.GITHUB
        ].token.get_secret_value()
        == 'test_token'
    )
    assert store1.secrets_store.provider_tokens[ProviderType.GITHUB].user_id is None

    # Test with dict token
    store2 = Secrets(
        provider_tokens={'github': {'token': 'test_token', 'user_id': 'user1'}}
    )
    assert (
        store2.provider_tokens[ProviderType.GITHUB].token.get_secret_value()
        == 'test_token'
    )
    assert store2.provider_tokens[ProviderType.GITHUB].user_id == 'user1'

    # Test with ProviderToken
    token = ProviderToken(token=SecretStr('test_token'), user_id='user2')
    store3 = Secrets(provider_tokens={ProviderType.GITHUB: token})
    assert (
        store3.provider_tokens[ProviderType.GITHUB].token.get_secret_value()
        == 'test_token'
    )
    assert store3.provider_tokens[ProviderType.GITHUB].user_id == 'user2'

    store4 = Secrets(
        provider_tokens={
            ProviderType.GITHUB: 123  # Invalid type
        }
    )

    assert ProviderType.GITHUB not in store4.provider_tokens

    # Test with empty/None token
    store5 = Secrets(provider_tokens={ProviderType.GITHUB: None})
    assert ProviderType.GITHUB not in store5.provider_tokens

    store6 = Secrets(
        provider_tokens={
            'invalid_provider': 'test_token'  # Invalid provider type
        }
    )

    assert len(store6.provider_tokens.keys()) == 0