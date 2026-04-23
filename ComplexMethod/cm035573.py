async def test_pagination_works_across_pages(self, mock_handler_cls):
        """Test that pagination works correctly across multiple pages.

        Note: This endpoint uses page-based pagination (passing page number to provider),
        not offset-based pagination like installations. The provider returns limit+1 items,
        and we check if there are more to determine next_page_id.
        """
        # Arrange
        mock_handler = MagicMock()

        # We'll set up the mock to return different data based on the page parameter
        # First call (page=1): return 3 items (limit+1), meaning there's a next page
        # Second call (page=2): return 3 items, meaning there's a next page
        # Third call (page=3): return 2 items, meaning it's the last page
        def mock_get_repositories(**kwargs):
            page = kwargs.get('page', 1)
            if page == 1:
                return [
                    Repository(
                        id=str(i),
                        full_name=f'user/repo{i}',
                        git_provider=ProviderType.GITHUB,
                        is_public=True,
                    )
                    for i in range(1, 4)  # 3 items = limit+1
                ]
            elif page == 2:
                return [
                    Repository(
                        id=str(i),
                        full_name=f'user/repo{i}',
                        git_provider=ProviderType.GITHUB,
                        is_public=True,
                    )
                    for i in range(4, 7)  # 3 items = limit+1
                ]
            else:
                return [
                    Repository(
                        id=str(i),
                        full_name=f'user/repo{i}',
                        git_provider=ProviderType.GITHUB,
                        is_public=True,
                    )
                    for i in range(7, 9)  # 2 items < limit+1 = last page
                ]

        mock_handler.get_repositories = AsyncMock(side_effect=mock_get_repositories)
        mock_handler_cls.return_value = mock_handler

        mock_context = _make_mock_user_context(
            provider_tokens={
                ProviderType.GITHUB: ProviderToken(user_id='user-123', token='token')
            },
            user_id='user-123',
        )

        # Act - First page (page=1)
        result_page1 = await search_repositories(
            provider=ProviderType.GITHUB,
            query=None,
            installation_id=None,
            page_id=None,  # This means page 1
            limit=2,
            sort_order=None,
            user_context=mock_context,
        )

        # Assert - First page returns 2 items (truncated from limit+1=3), with next_page_id
        assert len(result_page1.items) == 2
        assert result_page1.items[0].id == '1'
        assert result_page1.items[1].id == '2'
        assert result_page1.next_page_id == encode_page_id(2)

        # Act - Second page (page=2)
        result_page2 = await search_repositories(
            provider=ProviderType.GITHUB,
            query=None,
            installation_id=None,
            page_id=encode_page_id(2),  # This means page 2
            limit=2,
            sort_order=None,
            user_context=mock_context,
        )

        # Assert - Second page returns next 2 items
        assert len(result_page2.items) == 2
        assert result_page2.items[0].id == '4'
        assert result_page2.items[1].id == '5'
        # next_page_id = page + 1 = 2 + 1 = 3, encoded as base64 = 'Mw'
        assert result_page2.next_page_id == encode_page_id(3)