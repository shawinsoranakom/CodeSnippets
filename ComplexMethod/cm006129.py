async def test_read_project_consistent_response_structure(self, client: AsyncClient, logged_in_headers, basic_case):
        """Test that read_project returns consistent response structure in all cases."""
        # Create a project first
        create_response = await client.post("api/v1/projects/", json=basic_case, headers=logged_in_headers)
        assert create_response.status_code == status.HTTP_201_CREATED
        project_id = create_response.json()["id"]

        # Test multiple request scenarios to ensure consistency
        test_cases = [
            # No params - should return FolderReadWithFlows
            {"params": "", "expect_paginated": False},
            # Only search - should return FolderReadWithFlows
            {"params": "?search=test", "expect_paginated": False},
            # Only is_component - should return FolderReadWithFlows
            {"params": "?is_component=true", "expect_paginated": False},
            # Only is_flow - should return FolderReadWithFlows
            {"params": "?is_flow=true", "expect_paginated": False},
            # Only page - should return FolderReadWithFlows
            {"params": "?page=1", "expect_paginated": False},
            # Only size - should return FolderReadWithFlows
            {"params": "?size=10", "expect_paginated": False},
            # Both page and size - should return FolderWithPaginatedFlows
            {"params": "?page=1&size=10", "expect_paginated": True},
            # Page, size and filters - should return FolderWithPaginatedFlows
            {"params": "?page=1&size=10&is_flow=true", "expect_paginated": True},
        ]

        for test_case in test_cases:
            response = await client.get(f"api/v1/projects/{project_id}{test_case['params']}", headers=logged_in_headers)
            assert response.status_code == status.HTTP_200_OK, f"Failed for params: {test_case['params']}"

            result = response.json()
            assert isinstance(result, dict), f"Result should be dict for params: {test_case['params']}"

            if test_case["expect_paginated"]:
                # Paginated response structure
                assert "folder" in result, f"Paginated response missing 'folder' for params: {test_case['params']}"
                assert "flows" in result, f"Paginated response missing 'flows' for params: {test_case['params']}"
                assert "items" in result["flows"], f"Paginated flows missing 'items' for params: {test_case['params']}"
                assert "total" in result["flows"], f"Paginated flows missing 'total' for params: {test_case['params']}"
            else:
                # Non-paginated response structure
                assert "name" in result, f"Non-paginated response missing 'name' for params: {test_case['params']}"
                assert "flows" in result, f"Non-paginated response missing 'flows' for params: {test_case['params']}"
                # Should NOT have pagination structure
                assert "folder" not in result, (
                    f"Non-paginated response should not have 'folder' for params: {test_case['params']}"
                )