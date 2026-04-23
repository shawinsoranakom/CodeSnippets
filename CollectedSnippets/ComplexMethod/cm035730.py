def test_protocol_attributes_exist(self):
        """Test that protocol defines expected attributes."""
        client = TestableHTTPClient()

        # Test default attribute values from protocol
        assert hasattr(client, 'token')
        assert hasattr(client, 'refresh')
        assert hasattr(client, 'external_auth_id')
        assert hasattr(client, 'external_auth_token')
        assert hasattr(client, 'external_token_manager')
        assert hasattr(client, 'base_domain')

        # Test TestableHTTPClient values
        assert client.token == SecretStr('test-token')
        assert client.refresh is False
        assert client.external_auth_id is None
        assert client.external_auth_token is None
        assert client.external_token_manager is False
        assert client.base_domain is None