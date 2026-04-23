async def test_read_project_with_filtering_params(self, client: AsyncClient, logged_in_headers, basic_case):
        """Test read_project with filtering parameters (is_component, is_flow, search)."""
        # Create a project first
        create_response = await client.post("api/v1/projects/", json=basic_case, headers=logged_in_headers)
        assert create_response.status_code == status.HTTP_201_CREATED
        project_id = create_response.json()["id"]

        # Create a flow and component in the project for filtering tests
        flow_payload = {
            "name": "Test Flow",
            "description": "A test flow",
            "folder_id": project_id,
            "data": {"nodes": [], "edges": []},
            "is_component": False,
        }
        component_payload = {
            "name": "Test Component",
            "description": "A test component",
            "folder_id": project_id,
            "data": {"nodes": [], "edges": []},
            "is_component": True,
        }

        flow_response = await client.post("api/v1/flows/", json=flow_payload, headers=logged_in_headers)
        comp_response = await client.post("api/v1/flows/", json=component_payload, headers=logged_in_headers)
        assert flow_response.status_code == status.HTTP_201_CREATED
        assert comp_response.status_code == status.HTTP_201_CREATED

        # Test with filtering params but no pagination (should use non-paginated path)
        response = await client.get(f"api/v1/projects/{project_id}?is_flow=true", headers=logged_in_headers)
        assert response.status_code == status.HTTP_200_OK
        result = response.json()

        # Should return non-paginated response
        assert isinstance(result, dict)
        assert "name" in result
        assert "flows" in result

        # Test with filtering params AND pagination (should use paginated path)
        response = await client.get(
            f"api/v1/projects/{project_id}?is_flow=true&page=1&size=10", headers=logged_in_headers
        )
        assert response.status_code == status.HTTP_200_OK
        result = response.json()

        # Should return paginated response
        assert isinstance(result, dict)
        assert "folder" in result
        assert "flows" in result
        assert "items" in result["flows"]