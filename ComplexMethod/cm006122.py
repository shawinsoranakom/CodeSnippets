async def test_update_project_preserves_mixed_flows_and_components(client: AsyncClient, logged_in_headers):
    """Test that renaming a project preserves both flows and components correctly."""
    # Create a project
    project_payload = {
        "name": "Mixed Project",
        "description": "Testing mixed flows and components preservation",
        "flows_list": [],
        "components_list": [],
    }
    create_resp = await client.post("api/v1/projects/", json=project_payload, headers=logged_in_headers)
    assert create_resp.status_code == status.HTTP_201_CREATED
    project = create_resp.json()
    project_id = project["id"]

    # Create flows and components
    flow_payload = {
        "name": "Regular Flow",
        "description": "A regular flow",
        "folder_id": project_id,
        "data": {"nodes": [], "edges": []},
        "is_component": False,
    }
    component_payload = {
        "name": "Custom Component",
        "description": "A custom component",
        "folder_id": project_id,
        "data": {"nodes": [], "edges": []},
        "is_component": True,
    }

    flow_resp = await client.post("api/v1/flows/", json=flow_payload, headers=logged_in_headers)
    comp_resp = await client.post("api/v1/flows/", json=component_payload, headers=logged_in_headers)
    assert flow_resp.status_code == status.HTTP_201_CREATED
    assert comp_resp.status_code == status.HTTP_201_CREATED

    flow_id = flow_resp.json()["id"]
    comp_id = comp_resp.json()["id"]

    # Verify initial state
    get_resp = await client.get(f"api/v1/projects/{project_id}", headers=logged_in_headers)
    project_data = get_resp.json()

    flows_before = project_data.get("flows", [])
    actual_flows_before = [f for f in flows_before if not f.get("is_component", False)]
    components_before = [f for f in flows_before if f.get("is_component", False)]

    assert len(actual_flows_before) == 1
    assert len(components_before) == 1

    # Update project
    update_payload = {"name": "Renamed Mixed Project"}
    update_resp = await client.patch(f"api/v1/projects/{project_id}", json=update_payload, headers=logged_in_headers)
    assert update_resp.status_code == status.HTTP_200_OK

    # Verify both flows and components preserved
    get_after_resp = await client.get(f"api/v1/projects/{project_id}", headers=logged_in_headers)
    project_after = get_after_resp.json()

    flows_after = project_after.get("flows", [])
    actual_flows_after = [f for f in flows_after if not f.get("is_component", False)]
    components_after = [f for f in flows_after if f.get("is_component", False)]

    assert len(actual_flows_after) == 1, "Flow was lost after project rename!"
    assert len(components_after) == 1, "Component was lost after project rename!"

    flow_id_after = actual_flows_after[0]["id"]
    comp_id_after = components_after[0]["id"]

    assert str(flow_id) == flow_id_after
    assert str(comp_id) == comp_id_after