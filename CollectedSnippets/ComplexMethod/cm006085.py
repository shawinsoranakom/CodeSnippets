async def test_file_operations(files_client, files_created_api_key, files_flow):
    headers = {"x-api-key": files_created_api_key.api_key}
    flow_id = files_flow.id
    file_name = "test.txt"
    file_content = b"Hello, world!"

    # Step 1: Upload the file
    response = await files_client.post(
        f"api/v1/files/upload/{flow_id}",
        files={"file": (file_name, file_content)},
        headers=headers,
    )
    assert response.status_code == 201

    response_json = response.json()
    assert response_json["flowId"] == str(flow_id)

    # Check that the file_path matches the expected pattern
    file_path_pattern = re.compile(rf"{flow_id}/\d{{4}}-\d{{2}}-\d{{2}}_\d{{2}}-\d{{2}}-\d{{2}}_{file_name}")
    assert file_path_pattern.match(response_json["file_path"])

    # Extract the full file name with timestamp from the response
    full_file_name = response_json["file_path"].split("/")[-1]

    # Step 2: List files in the folder
    response = await files_client.get(f"api/v1/files/list/{files_flow.id}", headers=headers)
    assert response.status_code == 200
    assert full_file_name in response.json()["files"]

    # Step 3: Download the file and verify its content
    response = await files_client.get(f"api/v1/files/download/{files_flow.id}/{full_file_name}", headers=headers)
    assert response.status_code == 200
    assert response.content == file_content
    assert response.headers["content-type"] == "application/octet-stream"

    # Step 4: Delete the file
    response = await files_client.delete(f"api/v1/files/delete/{files_flow.id}/{full_file_name}", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"message": f"File {full_file_name} deleted successfully"}

    # Verify that the file is indeed deleted
    response = await files_client.get(f"api/v1/files/list/{files_flow.id}", headers=headers)
    assert full_file_name not in response.json()["files"]