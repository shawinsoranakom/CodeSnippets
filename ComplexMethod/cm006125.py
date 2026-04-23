async def test_read_project_without_pagination_params(self, client: AsyncClient, logged_in_headers, basic_case):
        """Test read_project returns correct response when no pagination params are provided."""
        # Create a project first
        create_response = await client.post("api/v1/projects/", json=basic_case, headers=logged_in_headers)
        assert create_response.status_code == status.HTTP_201_CREATED
        project_id = create_response.json()["id"]

        # Read project without pagination params
        response = await client.get(f"api/v1/projects/{project_id}", headers=logged_in_headers)

        assert response.status_code == status.HTTP_200_OK
        result = response.json()

        # Should return FolderReadWithFlows (direct project response)
        assert isinstance(result, dict)
        assert "name" in result
        assert "description" in result
        assert "id" in result
        assert "flows" in result
        assert result["name"] == basic_case["name"]