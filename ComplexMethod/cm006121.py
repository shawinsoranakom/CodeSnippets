async def test_update_project_preserves_components(client: AsyncClient, logged_in_headers):
    """Test that renaming a project preserves all associated components."""
    # Create a project
    project_payload = {
        "name": "Project with Components",
        "description": "Testing component preservation",
        "flows_list": [],
        "components_list": [],
    }
    create_resp = await client.post("api/v1/projects/", json=project_payload, headers=logged_in_headers)
    assert create_resp.status_code == status.HTTP_201_CREATED
    project = create_resp.json()
    project_id = project["id"]

    # Create components in the project
    comp1_payload = {
        "name": "Test Component 1",
        "description": "First test component",
        "folder_id": project_id,
        "data": {"nodes": [], "edges": []},
        "is_component": True,  # This makes it a component
    }
    comp2_payload = {
        "name": "Test Component 2",
        "description": "Second test component",
        "folder_id": project_id,
        "data": {"nodes": [], "edges": []},
        "is_component": True,  # This makes it a component
    }

    comp1_resp = await client.post("api/v1/flows/", json=comp1_payload, headers=logged_in_headers)
    comp2_resp = await client.post("api/v1/flows/", json=comp2_payload, headers=logged_in_headers)
    assert comp1_resp.status_code == status.HTTP_201_CREATED
    assert comp2_resp.status_code == status.HTTP_201_CREATED

    comp1_id = comp1_resp.json()["id"]
    comp2_id = comp2_resp.json()["id"]

    # Get project to verify components are associated
    get_resp = await client.get(f"api/v1/projects/{project_id}", headers=logged_in_headers)
    assert get_resp.status_code == status.HTTP_200_OK
    project_data = get_resp.json()

    # Current behavior: all flows (including components) are in the flows field
    flows_before = project_data.get("flows", [])
    # Filter only components
    components_before = [f for f in flows_before if f.get("is_component", False)]

    assert len(components_before) == 2
    component_ids_before = [c["id"] for c in components_before]
    assert str(comp1_id) in component_ids_before
    assert str(comp2_id) in component_ids_before

    # Update project name
    update_payload = {"name": "Renamed Project with Components"}
    update_resp = await client.patch(f"api/v1/projects/{project_id}", json=update_payload, headers=logged_in_headers)
    assert update_resp.status_code == status.HTTP_200_OK

    # Verify components are still associated after rename
    get_after_resp = await client.get(f"api/v1/projects/{project_id}", headers=logged_in_headers)
    assert get_after_resp.status_code == status.HTTP_200_OK
    project_after = get_after_resp.json()

    flows_after = project_after.get("flows", [])
    components_after = [f for f in flows_after if f.get("is_component", False)]

    assert len(components_after) == 2, (
        f"Expected 2 components after rename, got {len(components_after)}. Components lost!"
    )

    component_ids_after = [c["id"] for c in components_after]
    assert str(comp1_id) in component_ids_after, "Component 1 was lost after project rename!"
    assert str(comp2_id) in component_ids_after, "Component 2 was lost after project rename!"