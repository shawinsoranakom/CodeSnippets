async def test_search_repositories(forgejo_service):
    # Mock response data
    mock_repos_data = {
        'data': [
            {
                'id': 1,
                'full_name': 'test_user/repo1',
                'stars_count': 10,
            },
            {
                'id': 2,
                'full_name': 'test_user/repo2',
                'stars_count': 20,
            },
        ]
    }

    # Mock the _fetch_data method
    forgejo_service._make_request = AsyncMock(return_value=(mock_repos_data, {}))

    # Call the method
    repos = await forgejo_service.search_repositories(
        'test', 10, 'updated', 'desc', public=False, app_mode=AppMode.OPENHANDS
    )

    # Verify the result
    assert len(repos) == 2
    assert all(isinstance(repo, Repository) for repo in repos)
    assert repos[0].id == '1'
    assert repos[0].full_name == 'test_user/repo1'
    assert repos[0].stargazers_count == 10
    assert repos[0].git_provider == ProviderType.FORGEJO
    assert repos[1].id == '2'
    assert repos[1].full_name == 'test_user/repo2'
    assert repos[1].stargazers_count == 20
    assert repos[1].git_provider == ProviderType.FORGEJO

    # Verify the _fetch_data call
    forgejo_service._make_request.assert_called_once_with(
        f'{forgejo_service.BASE_URL}/repos/search',
        {
            'q': 'test',
            'limit': 10,
            'sort': 'updated',
            'order': 'desc',
            'mode': 'source',
        },
    )