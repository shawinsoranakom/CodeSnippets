async def test_bitbucket_get_repositories_mixed_owner_types():
    """Test that get_repositories correctly handles mixed user and organization repositories."""
    service = BitBucketService(token=SecretStr('test-token'))

    # Mock repository data with mixed workspace types
    mock_workspaces = [
        {'slug': 'test-user', 'name': 'Test User'},
        {'slug': 'test-org', 'name': 'Test Organization'},
    ]

    # First workspace (user) repositories
    mock_user_repos = [
        {
            'uuid': 'repo-1',
            'slug': 'user-repo',
            'workspace': {'slug': 'test-user', 'is_private': True},
            'is_private': False,
            'updated_on': '2023-01-01T00:00:00Z',
        }
    ]

    # Second workspace (organization) repositories
    mock_org_repos = [
        {
            'uuid': 'repo-2',
            'slug': 'org-repo',
            'workspace': {'slug': 'test-org', 'is_private': False},
            'is_private': False,
            'updated_on': '2023-01-02T00:00:00Z',
        }
    ]

    with patch.object(service, '_fetch_paginated_data') as mock_fetch:
        mock_fetch.side_effect = [mock_workspaces, mock_user_repos, mock_org_repos]

        repositories = await service.get_all_repositories('pushed', AppMode.SAAS)

        # Verify we got repositories from both workspaces
        assert len(repositories) == 2

        # Verify owner_type is correctly set for each repository
        user_repo = next(repo for repo in repositories if 'user-repo' in repo.full_name)
        org_repo = next(repo for repo in repositories if 'org-repo' in repo.full_name)

        assert user_repo.owner_type == OwnerType.ORGANIZATION
        assert org_repo.owner_type == OwnerType.ORGANIZATION