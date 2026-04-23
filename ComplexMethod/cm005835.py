async def test_read_folder_with_flows(client: AsyncClient, json_flow: str, logged_in_headers):
    # Create a new project
    folder_name = f"Test Project {uuid4()}"
    flow_name = f"Test Flow {uuid4()}"
    project = FolderCreate(name=folder_name, description="Test project description")
    response = await client.post("api/v1/projects/", json=project.model_dump(), headers=logged_in_headers)
    assert response.status_code == 201
    created_folder = response.json()
    folder_id = created_folder["id"]

    # Create a flow in the project
    flow_data = orjson.loads(json_flow)
    data = flow_data["data"]
    flow = FlowCreate(name=flow_name, description="description", data=data)
    flow.folder_id = folder_id
    response = await client.post("api/v1/flows/", json=flow.model_dump(), headers=logged_in_headers)
    assert response.status_code == 201

    # Read the project with flows
    response = await client.get(f"api/v1/projects/{folder_id}", headers=logged_in_headers)
    assert response.status_code == 200
    folder_data = response.json()
    assert folder_data["name"] == folder_name
    assert folder_data["description"] == "Test project description"
    assert len(folder_data["flows"]) == 1
    assert folder_data["flows"][0]["name"] == flow_name