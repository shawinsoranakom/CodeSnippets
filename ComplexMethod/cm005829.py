async def test_get_flows_from_folder_pagination(client: AsyncClient, logged_in_headers):
    # Create a new project
    folder_name = f"Test Project {uuid4()}"
    project = FolderCreate(name=folder_name, description="Test project description", components_list=[], flows_list=[])

    response = await client.post("api/v1/projects/", json=project.model_dump(), headers=logged_in_headers)
    assert response.status_code == 201, f"Expected status code 201, but got {response.status_code}"

    created_folder = response.json()
    folder_id = created_folder["id"]

    response = await client.get(
        f"api/v1/projects/{folder_id}", headers=logged_in_headers, params={"page": 1, "size": 50}
    )
    assert response.status_code == 200
    assert response.json()["folder"]["name"] == folder_name
    assert response.json()["folder"]["description"] == "Test project description"
    assert response.json()["flows"]["page"] == 1
    assert response.json()["flows"]["size"] == 50
    assert response.json()["flows"]["pages"] == 0
    assert response.json()["flows"]["total"] == 0
    assert len(response.json()["flows"]["items"]) == 0