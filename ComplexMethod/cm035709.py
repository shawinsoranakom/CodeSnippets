def test_initializing_custom_secrets_with_mixed_value_types(self):
        """Test initializing custom secrets with both plain strings and SecretStr objects."""
        # Create custom secrets with mixed value types
        custom_secrets_dict = {
            'API_KEY': {
                'secret': 'api-key-123',
                'description': 'API key',
            },  # Dict format
            'DATABASE_PASSWORD': CustomSecret(
                secret=SecretStr('db-pass-456'), description='DB password'
            ),  # CustomSecret object
        }

        # Initialize the store
        store = Secrets(custom_secrets=custom_secrets_dict)

        # Verify all secrets are converted to CustomSecret objects
        assert isinstance(store.custom_secrets, MappingProxyType)
        assert len(store.custom_secrets) == 2

        # Check API_KEY (was dict)
        assert isinstance(store.custom_secrets['API_KEY'], CustomSecret)
        assert (
            store.custom_secrets['API_KEY'].secret.get_secret_value() == 'api-key-123'
        )
        assert store.custom_secrets['API_KEY'].description == 'API key'

        # Check DATABASE_PASSWORD (was CustomSecret)
        assert isinstance(store.custom_secrets['DATABASE_PASSWORD'], CustomSecret)
        assert (
            store.custom_secrets['DATABASE_PASSWORD'].secret.get_secret_value()
            == 'db-pass-456'
        )
        assert store.custom_secrets['DATABASE_PASSWORD'].description == 'DB password'