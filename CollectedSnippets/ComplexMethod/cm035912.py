async def test_encryption_decryption(self, mock_get_user, secrets_store, mock_user):
        # Setup mock
        mock_get_user.return_value = mock_user
        # Create a Secrets object with sensitive data
        user_secrets = Secrets(
            custom_secrets=MappingProxyType(
                {
                    'api_token': CustomSecret.from_value(
                        {'secret': 'sensitive_token', 'description': ''}
                    ),
                    'secret_key': CustomSecret.from_value(
                        {'secret': 'sensitive_secret', 'description': ''}
                    ),
                    'normal_data': CustomSecret.from_value(
                        {'secret': 'not_sensitive', 'description': ''}
                    ),
                }
            )
        )

        assert (
            user_secrets.custom_secrets['api_token'].secret.get_secret_value()
            == 'sensitive_token'
        )
        # Store the secrets
        await secrets_store.store(user_secrets)

        # Verify the data is encrypted in the database
        from sqlalchemy import select

        async with secrets_store.a_session_maker() as session:
            result = await session.execute(
                select(StoredCustomSecrets)
                .filter(StoredCustomSecrets.keycloak_user_id == 'user-id')
                .filter(StoredCustomSecrets.org_id == mock_user.current_org_id)
            )
            stored = result.scalars().first()

            # The sensitive data should be encrypted
            assert stored.secret_value != 'sensitive_token'
            assert stored.secret_value != 'sensitive_secret'
            assert stored.secret_value != 'not_sensitive'

        # Load the secrets and verify decryption works
        loaded_secrets = await secrets_store.load()
        assert (
            loaded_secrets.custom_secrets['api_token'].secret.get_secret_value()
            == 'sensitive_token'
        )
        assert (
            loaded_secrets.custom_secrets['secret_key'].secret.get_secret_value()
            == 'sensitive_secret'
        )
        assert (
            loaded_secrets.custom_secrets['normal_data'].secret.get_secret_value()
            == 'not_sensitive'
        )