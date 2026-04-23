def test_protocol_methods_exist(self):
        """Test that protocol defines expected methods."""
        client = TestableHTTPClient()

        # Test that methods exist
        assert hasattr(client, 'get_latest_token')
        assert hasattr(client, '_get_headers')
        assert hasattr(client, '_make_request')
        assert hasattr(client, '_has_token_expired')
        assert hasattr(client, 'execute_request')
        assert hasattr(client, 'handle_http_status_error')
        assert hasattr(client, 'handle_http_error')
        assert hasattr(client, 'provider')