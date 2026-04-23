async def test_search_repositories_returns_repos_from_provider(
        self, mock_provider_handler_class, slack_manager, mock_user_auth
    ):
        """Test that _search_repositories returns repositories from the provider."""

        # Setup: Create real Repository objects
        expected_repos = [
            Repository(
                id='1',
                full_name='owner/frontend-app',
                git_provider=ProviderType.GITHUB,
                is_public=True,
            ),
            Repository(
                id='2',
                full_name='owner/backend-api',
                git_provider=ProviderType.GITHUB,
                is_public=False,
            ),
            Repository(
                id='3',
                full_name='owner/shared-lib',
                git_provider=ProviderType.GITHUB,
                is_public=True,
            ),
        ]

        # Setup: Mock provider handler to return real repos
        mock_provider_handler = MagicMock()
        mock_provider_handler.search_repositories = AsyncMock(
            return_value=expected_repos
        )
        mock_provider_handler_class.return_value = mock_provider_handler

        # Setup: Mock user_auth to return valid tokens
        mock_user_auth.get_provider_tokens = AsyncMock(
            return_value={'github': 'test-token'}
        )
        mock_user_auth.get_access_token = AsyncMock(return_value='access-token')
        mock_user_auth.get_user_id = AsyncMock(return_value='user-123')

        # Execute: Search with a query
        result = await slack_manager._search_repositories(
            mock_user_auth, query='frontend', per_page=20
        )

        # Verify: The correct parameters were passed to search_repositories
        mock_provider_handler.search_repositories.assert_called_once()
        call_kwargs = mock_provider_handler.search_repositories.call_args[1]
        assert call_kwargs['query'] == 'frontend'
        assert call_kwargs['per_page'] == 20
        assert call_kwargs['sort'] == 'pushed'
        assert call_kwargs['order'] == 'desc'

        # Verify: All repos are returned
        assert len(result) == 3
        assert result[0].full_name == 'owner/frontend-app'
        assert result[1].full_name == 'owner/backend-api'
        assert result[2].full_name == 'owner/shared-lib'