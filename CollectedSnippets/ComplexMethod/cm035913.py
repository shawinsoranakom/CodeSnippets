async def test_encrypt_decrypt_kwargs(self, secrets_store):
        # Test encryption and decryption directly
        test_data: dict[str, Any] = {
            'api_token': 'test_token',
            'client_secret': 'test_secret',
            'normal_data': 'not_sensitive',
            'nested': {
                'nested_token': 'nested_secret_value',
                'nested_normal': 'nested_normal_value',
            },
        }

        # Encrypt the data
        secrets_store._encrypt_kwargs(test_data)

        # Sensitive data is encrypted
        assert test_data['api_token'] != 'test_token'
        assert test_data['client_secret'] != 'test_secret'
        assert test_data['normal_data'] != 'not_sensitive'
        assert test_data['nested']['nested_token'] != 'nested_secret_value'
        assert test_data['nested']['nested_normal'] != 'nested_normal_value'

        # Decrypt the data
        secrets_store._decrypt_kwargs(test_data)

        # Verify sensitive data is properly decrypted
        assert test_data['api_token'] == 'test_token'
        assert test_data['client_secret'] == 'test_secret'
        assert test_data['normal_data'] == 'not_sensitive'
        assert test_data['nested']['nested_token'] == 'nested_secret_value'
        assert test_data['nested']['nested_normal'] == 'nested_normal_value'