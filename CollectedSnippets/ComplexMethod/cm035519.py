async def test_get_all_repositories(forgejo_service):
    # Mock response data for first page
    mock_repos_data_page1 = [
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

    # Mock response data for second page
    mock_repos_data_page2 = [
        {
            'id': 3,
            'full_name': 'test_user/repo3',
            'stars_count': 30,
        },
    ]

    # Mock the _fetch_data method to return different data for different pages
    forgejo_service._make_request = AsyncMock()
    forgejo_service._make_request.side_effect = [
        (
            mock_repos_data_page1,
            {'Link': '<https://codeberg.org/api/v1/user/repos?page=2>; rel="next"'},
        ),
        (mock_repos_data_page2, {'Link': ''}),
    ]

    # Call the method
    repos = await forgejo_service.get_all_repositories('updated', AppMode.OPENHANDS)

    # Verify the result
    assert len(repos) == 3
    assert all(isinstance(repo, Repository) for repo in repos)
    assert repos[0].id == '1'
    assert repos[0].full_name == 'test_user/repo1'
    assert repos[0].stargazers_count == 10
    assert repos[0].git_provider == ProviderType.FORGEJO
    assert repos[1].id == '2'
    assert repos[1].full_name == 'test_user/repo2'
    assert repos[1].stargazers_count == 20
    assert repos[1].git_provider == ProviderType.FORGEJO
    assert repos[2].id == '3'
    assert repos[2].full_name == 'test_user/repo3'
    assert repos[2].stargazers_count == 30
    assert repos[2].git_provider == ProviderType.FORGEJO

    # Verify the _fetch_data calls
    assert forgejo_service._make_request.call_count == 2
    forgejo_service._make_request.assert_any_call(
        f'{forgejo_service.BASE_URL}/user/repos',
        {'page': '1', 'limit': '100', 'sort': 'updated'},
    )
    forgejo_service._make_request.assert_any_call(
        f'{forgejo_service.BASE_URL}/user/repos',
        {'page': '2', 'limit': '100', 'sort': 'updated'},
    )