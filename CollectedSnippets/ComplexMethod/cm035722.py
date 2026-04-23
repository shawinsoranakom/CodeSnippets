async def test_bitbucket_pagination():
    """Test that the Bitbucket service correctly handles pagination for repositories."""
    # Create a service instance
    service = BitBucketService(token=SecretStr('test-token'))

    # Mock the _make_request method to simulate paginated responses
    with patch.object(service, '_make_request') as mock_request:
        # Mock responses for pagination test
        mock_request.side_effect = [
            # First call: workspaces
            ({'values': [{'slug': 'test-workspace', 'name': 'Test Workspace'}]}, {}),
            # Second call: first page of repositories
            (
                {
                    'values': [
                        {
                            'uuid': 'repo-1',
                            'slug': 'repo1',
                            'workspace': {'slug': 'test-workspace'},
                            'is_private': False,
                            'updated_on': '2023-01-01T00:00:00Z',
                        },
                        {
                            'uuid': 'repo-2',
                            'slug': 'repo2',
                            'workspace': {'slug': 'test-workspace'},
                            'is_private': True,
                            'updated_on': '2023-01-02T00:00:00Z',
                        },
                    ],
                    'next': 'https://api.bitbucket.org/2.0/repositories/test-workspace?page=2',
                },
                {},
            ),
            # Third call: second page of repositories
            (
                {
                    'values': [
                        {
                            'uuid': 'repo-3',
                            'slug': 'repo3',
                            'workspace': {'slug': 'test-workspace'},
                            'is_private': False,
                            'updated_on': '2023-01-03T00:00:00Z',
                        }
                    ],
                    # No 'next' URL indicates this is the last page
                },
                {},
            ),
        ]

        # Call get_repositories
        repositories = await service.get_all_repositories('pushed', AppMode.SAAS)

        # Verify that all three requests were made (workspaces + 2 pages of repos)
        assert mock_request.call_count == 3

        # Verify that we got all repositories from both pages
        assert len(repositories) == 3
        assert repositories[0].id == 'repo-1'
        assert repositories[1].id == 'repo-2'
        assert repositories[2].id == 'repo-3'

        # Verify repository properties
        assert repositories[0].full_name == 'test-workspace/repo1'
        assert repositories[0].is_public is True
        assert repositories[1].is_public is False
        assert repositories[2].is_public is True