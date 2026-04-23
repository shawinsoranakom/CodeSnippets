async def test_search_repositories_with_query(self, mock_handler_cls):
        """Test repository search when query is provided.

        This tests the search path (with query) which calls search_repositories
        instead of get_repositories, and verifies sort_order is parsed correctly.
        """
        # Arrange
        mock_handler = MagicMock()
        mock_handler.search_repositories = AsyncMock(
            return_value=[
                Repository(
                    id='10',
                    full_name='org/searched-repo',
                    git_provider=ProviderType.GITHUB,
                    is_public=True,
                ),
                Repository(
                    id='11',
                    full_name='user/searched-repo',
                    git_provider=ProviderType.GITHUB,
                    is_public=False,
                ),
            ]
        )
        mock_handler_cls.return_value = mock_handler

        mock_context = _make_mock_user_context(
            provider_tokens={
                ProviderType.GITHUB: ProviderToken(user_id='user-123', token='token')
            },
            user_id='user-123',
        )

        # Act - call with query and sort_order to trigger search path
        result = await search_repositories(
            provider=ProviderType.GITHUB,
            query='my-search-term',
            installation_id=None,
            page_id=None,
            limit=10,
            sort_order=SortOrder.STAR_DESC,  # This should be parsed into sort='stars', order='desc'
            user_context=mock_context,
        )

        # Assert - verify search_repositories was called (not get_repositories)
        mock_handler.search_repositories.assert_called_once()
        call_kwargs = mock_handler.search_repositories.call_args.kwargs

        # Verify query is passed
        assert call_kwargs.get('query') == 'my-search-term'

        # Verify sort and order are parsed from sort_order ('stars-desc' -> sort='stars', order='desc')
        assert call_kwargs.get('sort') == 'stars'
        assert call_kwargs.get('order') == 'desc'

        # Verify per_page is limit + 1
        assert call_kwargs.get('per_page') == 11

        # Verify results are returned
        assert len(result.items) == 2
        assert result.items[0].id == '10'
        assert result.items[1].id == '11'