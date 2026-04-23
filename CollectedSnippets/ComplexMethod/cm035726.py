async def test_gitlab_get_repositories_mixed_owner_types():
    """Test that get_repositories correctly handles mixed user and organization repositories."""
    service = GitLabService(token=SecretStr('test-token'))

    # Mock repository data with mixed namespace types
    mock_repos = [
        {
            'id': 123,
            'path_with_namespace': 'test-user/user-repo',
            'star_count': 10,
            'visibility': 'public',
            'namespace': {'kind': 'user'},  # User namespace
        },
        {
            'id': 456,
            'path_with_namespace': 'test-org/org-repo',
            'star_count': 25,
            'visibility': 'public',
            'namespace': {'kind': 'group'},  # Organization/Group namespace
        },
    ]

    with patch.object(service, '_make_request') as mock_request:
        # Mock the pagination response
        mock_request.side_effect = [(mock_repos, {'Link': ''})]  # No next page

        repositories = await service.get_all_repositories('pushed', AppMode.SAAS)

        # Verify we got the expected number of repositories
        assert len(repositories) == 2

        # Verify owner_type is correctly set for each repository
        user_repo = next(repo for repo in repositories if 'user-repo' in repo.full_name)
        org_repo = next(repo for repo in repositories if 'org-repo' in repo.full_name)

        assert user_repo.owner_type == OwnerType.USER
        assert org_repo.owner_type == OwnerType.ORGANIZATION