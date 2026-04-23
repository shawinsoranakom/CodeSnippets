async def test_update_project_preserves_flows(client: AsyncClient, logged_in_headers):
    """Test that renaming a project preserves all associated flows (regression test for flow loss bug)."""
    # Create a project
    project_payload = {
        "name": "Project with Flows",
        "description": "Testing flow preservation",
        "flows_list": [],
        "components_list": [],
    }
    create_resp = await client.post("api/v1/projects/", json=project_payload, headers=logged_in_headers)
    assert create_resp.status_code == status.HTTP_201_CREATED
    project = create_resp.json()
    project_id = project["id"]

    # Create flows in the project
    flow1_payload = {
        "name": "Test Flow 1",
        "description": "First test flow",
        "folder_id": project_id,
        "data": {"nodes": [], "edges": []},
        "is_component": False,
    }
    flow2_payload = {
        "name": "Test Flow 2",
        "description": "Second test flow",
        "folder_id": project_id,
        "data": {"nodes": [], "edges": []},
        "is_component": False,
    }

    flow1_resp = await client.post("api/v1/flows/", json=flow1_payload, headers=logged_in_headers)
    flow2_resp = await client.post("api/v1/flows/", json=flow2_payload, headers=logged_in_headers)
    assert flow1_resp.status_code == status.HTTP_201_CREATED
    assert flow2_resp.status_code == status.HTTP_201_CREATED

    flow1_id = flow1_resp.json()["id"]
    flow2_id = flow2_resp.json()["id"]

    # Get project to verify flows are associated
    get_resp = await client.get(f"api/v1/projects/{project_id}", headers=logged_in_headers)
    assert get_resp.status_code == status.HTTP_200_OK
    project_data = get_resp.json()

    # Current behavior: all flows (including components) are in the flows field
    flows_before = project_data.get("flows", [])
    # Filter only actual flows (not components)
    actual_flows_before = [f for f in flows_before if not f.get("is_component", False)]

    assert len(actual_flows_before) == 2
    flow_ids_before = [f["id"] for f in actual_flows_before]
    assert str(flow1_id) in flow_ids_before
    assert str(flow2_id) in flow_ids_before

    # Update project name (the bug scenario)
    update_payload = {"name": "Renamed Project with Flows", "description": "Testing flow preservation after rename"}
    update_resp = await client.patch(f"api/v1/projects/{project_id}", json=update_payload, headers=logged_in_headers)
    assert update_resp.status_code == status.HTTP_200_OK

    # Verify project was renamed
    updated_project = update_resp.json()
    assert updated_project["name"] == "Renamed Project with Flows"

    # Critical test: Verify flows are still associated after rename
    get_after_resp = await client.get(f"api/v1/projects/{project_id}", headers=logged_in_headers)
    assert get_after_resp.status_code == status.HTTP_200_OK
    project_after = get_after_resp.json()

    flows_after = project_after.get("flows", [])
    actual_flows_after = [f for f in flows_after if not f.get("is_component", False)]

    # This was the bug: flows were being lost after project rename
    assert len(actual_flows_after) == 2, f"Expected 2 flows after rename, got {len(actual_flows_after)}. Flows lost!"

    flow_ids_after = [f["id"] for f in actual_flows_after]
    assert str(flow1_id) in flow_ids_after, "Flow 1 was lost after project rename!"
    assert str(flow2_id) in flow_ids_after, "Flow 2 was lost after project rename!"

    # Verify individual flows still exist and are accessible
    flow1_get_resp = await client.get(f"api/v1/flows/{flow1_id}", headers=logged_in_headers)
    flow2_get_resp = await client.get(f"api/v1/flows/{flow2_id}", headers=logged_in_headers)
    assert flow1_get_resp.status_code == status.HTTP_200_OK
    assert flow2_get_resp.status_code == status.HTTP_200_OK

    # Verify flows still reference the correct project
    flow1_data = flow1_get_resp.json()
    flow2_data = flow2_get_resp.json()
    assert str(flow1_data["folder_id"]) == str(project_id)
    assert str(flow2_data["folder_id"]) == str(project_id)