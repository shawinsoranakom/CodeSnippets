async def test_azure_devops_get_repositories():
    """Test that the Azure DevOps service can get repositories."""
    with patch('httpx.AsyncClient') as mock_client:
        # Mock the response for projects
        mock_projects_response = MagicMock()
        mock_projects_response.json.return_value = {
            'value': [
                {'name': 'Project1'},
            ]
        }
        mock_projects_response.raise_for_status = AsyncMock()

        # Mock the response for repositories
        mock_repos_response = MagicMock()
        mock_repos_response.json.return_value = {
            'value': [
                {
                    'id': 'repo1',
                    'name': 'Repo1',
                    'project': {'name': 'Project1'},
                    'lastUpdateTime': '2023-01-01T00:00:00Z',
                },
                {
                    'id': 'repo2',
                    'name': 'Repo2',
                    'project': {'name': 'Project1'},
                    'lastUpdateTime': '2023-01-02T00:00:00Z',
                },
            ]
        }
        mock_repos_response.raise_for_status = AsyncMock()

        # Set up the mock client to return our mock responses
        # First call: get projects, Second call: get repos for Project1
        mock_client_instance = MagicMock()
        mock_client_instance.get = AsyncMock(
            side_effect=[
                mock_projects_response,
                mock_repos_response,
            ]
        )
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        # Create the service and call get_repositories
        service = AzureDevOpsService(
            user_id='test_user',
            token=None,
            base_domain='myorg',
        )

        # Mock the _get_azure_devops_headers method
        service._get_azure_devops_headers = AsyncMock(return_value={})

        # Call the method
        repos = await service.get_repositories('updated', None)

        # Verify the results (sorted by lastUpdateTime descending, so repo2 first)
        assert len(repos) == 2
        assert repos[0].id == 'repo2'
        assert repos[0].full_name == 'myorg/Project1/Repo2'
        assert repos[0].git_provider == ProviderType.AZURE_DEVOPS
        assert repos[1].id == 'repo1'
        assert repos[1].full_name == 'myorg/Project1/Repo1'
        assert repos[1].git_provider == ProviderType.AZURE_DEVOPS