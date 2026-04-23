async def test_read_folder_with_pagination(client: AsyncClient, logged_in_headers):
    # Create a new project
    folder_name = f"Test Project {uuid4()}"
    project = FolderCreate(name=folder_name, description="Test project description")
    response = await client.post("api/v1/projects/", json=project.model_dump(), headers=logged_in_headers)
    assert response.status_code == 201
    created_folder = response.json()
    folder_id = created_folder["id"]

    # Read the project with pagination
    response = await client.get(
        f"api/v1/projects/{folder_id}", headers=logged_in_headers, params={"page": 1, "size": 10}
    )
    assert response.status_code == 200
    folder_data = response.json()
    assert isinstance(folder_data, dict)
    assert "folder" in folder_data
    assert "flows" in folder_data
    assert folder_data["folder"]["name"] == folder_name
    assert folder_data["folder"]["description"] == "Test project description"
    assert folder_data["flows"]["page"] == 1
    assert folder_data["flows"]["size"] == 10
    assert isinstance(folder_data["flows"]["items"], list)