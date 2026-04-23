async def test_read_project_with_partial_pagination_params(
        self, client: AsyncClient, logged_in_headers, basic_case
    ):
        """Test read_project behavior when only some pagination params are provided."""
        # Create a project first
        create_response = await client.post("api/v1/projects/", json=basic_case, headers=logged_in_headers)
        assert create_response.status_code == status.HTTP_201_CREATED
        project_id = create_response.json()["id"]

        # Test with only page param (no size)
        response = await client.get(f"api/v1/projects/{project_id}?page=1", headers=logged_in_headers)
        assert response.status_code == status.HTTP_200_OK
        result = response.json()

        # Should return non-paginated response (FolderReadWithFlows)
        assert isinstance(result, dict)
        assert "name" in result  # Direct project response
        assert "flows" in result
        assert result["name"] == basic_case["name"]

        # Test with only size param (no page)
        response = await client.get(f"api/v1/projects/{project_id}?size=10", headers=logged_in_headers)
        assert response.status_code == status.HTTP_200_OK
        result = response.json()

        # Should return non-paginated response (FolderReadWithFlows)
        assert isinstance(result, dict)
        assert "name" in result  # Direct project response
        assert "flows" in result
        assert result["name"] == basic_case["name"]