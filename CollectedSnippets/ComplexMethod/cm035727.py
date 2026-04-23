async def test_gitlab_search_repositories_uses_membership_and_min_access_level():
    """Test that search_repositories uses membership and min_access_level for non-public searches."""
    service = GitLabService(token=SecretStr('test-token'))

    # Mock repository data
    mock_repos = [
        {
            'id': 123,
            'path_with_namespace': 'test-user/search-repo1',
            'star_count': 10,
            'visibility': 'private',
            'namespace': {'kind': 'user'},
        },
        {
            'id': 456,
            'path_with_namespace': 'test-org/search-repo2',
            'star_count': 25,
            'visibility': 'private',
            'namespace': {'kind': 'group'},
        },
    ]

    with patch.object(service, '_make_request') as mock_request:
        mock_request.return_value = (mock_repos, {})

        # Test non-public search (should use membership and min_access_level)
        repositories = await service.search_repositories(
            query='test-query', per_page=30, sort='updated', order='desc', public=False
        )

        # Verify the request was made with correct parameters
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        url = call_args[0][0]
        params = call_args[0][1]  # params is the second positional argument

        assert url == f'{service.BASE_URL}/projects'
        assert params['search'] == 'test-query'
        assert params['per_page'] == '30'  # GitLab service converts to string
        assert params['order_by'] == 'last_activity_at'
        assert params['sort'] == 'desc'
        assert params['membership'] is True
        assert params['search_namespaces'] is True  # Added by implementation
        assert 'min_access_level' not in params  # Not set by current implementation
        assert 'owned' not in params
        assert 'visibility' not in params

        # Verify we got the expected repositories
        assert len(repositories) == 2