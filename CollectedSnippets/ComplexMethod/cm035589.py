async def test_returns_secret_names_without_values(self):
        """Response contains names and descriptions, NOT raw values."""
        secrets = {
            'GITHUB_TOKEN': StaticSecret(
                value=SecretStr('ghp_test123'),
                description='GitHub personal access token',
            ),
            'MY_API_KEY': StaticSecret(
                value=SecretStr('my-api-key-value'),
                description='Custom API key',
            ),
        }
        sandbox_info = _make_sandbox_info()

        with patch(
            'openhands.app_server.sandbox.sandbox_router._get_user_context'
        ) as mock_ctx:
            ctx = AsyncMock()
            ctx.get_secrets = AsyncMock(return_value=secrets)
            ctx.get_provider_tokens = AsyncMock(return_value={})
            mock_ctx.return_value = ctx

            result = await list_secret_names(sandbox_info=sandbox_info)

        assert isinstance(result, SecretNamesResponse)
        assert len(result.secrets) == 2
        names = {s.name for s in result.secrets}
        assert 'GITHUB_TOKEN' in names
        assert 'MY_API_KEY' in names

        gh = next(s for s in result.secrets if s.name == 'GITHUB_TOKEN')
        assert gh.description == 'GitHub personal access token'
        # Verify no 'value' field is exposed
        assert not hasattr(gh, 'value')