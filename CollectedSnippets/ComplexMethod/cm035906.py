def test_set_response_cookie(mock_response, mock_request):
    """Test setting the auth cookie on a response."""

    with (
        patch('server.routes.auth.config') as mock_config,
        patch('server.utils.url_utils.get_global_config') as get_global_config,
    ):
        mock_config.jwt_secret.get_secret_value.return_value = 'test_secret'
        get_global_config.return_value = MagicMock(web_url='https://example.com')

        set_response_cookie(
            request=mock_request,
            response=mock_response,
            keycloak_access_token='test_access_token',
            keycloak_refresh_token='test_refresh_token',
            secure=True,
            accepted_tos=True,
        )

        mock_response.set_cookie.assert_called_once()
        args, kwargs = mock_response.set_cookie.call_args

        assert kwargs['key'] == 'keycloak_auth'
        assert 'value' in kwargs
        assert kwargs['httponly'] is True
        assert kwargs['secure'] is True
        assert kwargs['samesite'] == 'strict'
        assert kwargs['domain'] == 'example.com'

        # Verify the JWT token contains the correct data
        token_data = jwt.decode(kwargs['value'], 'test_secret', algorithms=['HS256'])
        assert token_data['access_token'] == 'test_access_token'
        assert token_data['refresh_token'] == 'test_refresh_token'
        assert token_data['accepted_tos'] is True