async def test_read_project_with_pagination_params(self, client: AsyncClient, logged_in_headers, basic_case):
        """Test read_project returns paginated response when pagination params are provided."""
        # Create a project first
        create_response = await client.post("api/v1/projects/", json=basic_case, headers=logged_in_headers)
        assert create_response.status_code == status.HTTP_201_CREATED
        project_id = create_response.json()["id"]

        # Read project with pagination params
        response = await client.get(f"api/v1/projects/{project_id}?page=1&size=10", headers=logged_in_headers)

        assert response.status_code == status.HTTP_200_OK
        result = response.json()

        # Should return FolderWithPaginatedFlows (paginated response)
        assert isinstance(result, dict)
        assert "folder" in result
        assert "flows" in result

        # Check folder structure
        folder = result["folder"]
        assert "name" in folder
        assert "description" in folder
        assert "id" in folder
        assert folder["name"] == basic_case["name"]

        # Check flows pagination structure
        flows = result["flows"]
        assert "items" in flows
        assert "total" in flows
        assert "page" in flows
        assert "size" in flows