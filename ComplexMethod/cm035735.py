async def test_github_get_repositories_mixed_owner_types():
    """Test that get_repositories correctly handles mixed user and organization repositories."""
    service = GitHubService(user_id=None, token=SecretStr('test-token'))

    # Mock repository data with mixed owner types
    mock_repo_data = [
        {
            'id': 123,
            'full_name': 'test-user/user-repo',
            'private': False,
            'stargazers_count': 10,
            'owner': {'type': 'User'},  # User repository
        },
        {
            'id': 456,
            'full_name': 'test-org/org-repo',
            'private': True,
            'stargazers_count': 25,
            'owner': {'type': 'Organization'},  # Organization repository
        },
    ]

    with (
        patch.object(service, '_fetch_paginated_repos', return_value=mock_repo_data),
        patch.object(service, 'get_installations', return_value=[123]),
    ):
        repositories = await service.get_all_repositories('pushed', AppMode.SAAS)

        # Verify we got the expected number of repositories
        assert len(repositories) == 2

        # Verify owner_type is correctly set for each repository
        user_repo = next(repo for repo in repositories if 'user-repo' in repo.full_name)
        org_repo = next(repo for repo in repositories if 'org-repo' in repo.full_name)

        assert user_repo.owner_type == OwnerType.USER
        assert org_repo.owner_type == OwnerType.ORGANIZATION