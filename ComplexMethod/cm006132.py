async def test_upload_list_delete_and_validate_files(files_client, files_created_api_key):
    headers = {"x-api-key": files_created_api_key.api_key}

    # Upload two files
    response1 = await files_client.post(
        "api/v2/files",
        files={"file": ("file1.txt", b"content1")},
        headers=headers,
    )
    assert response1.status_code == 201
    file1 = response1.json()

    response2 = await files_client.post(
        "api/v2/files",
        files={"file": ("file2.txt", b"content2")},
        headers=headers,
    )
    assert response2.status_code == 201
    file2 = response2.json()

    # List files and validate both are present
    response = await files_client.get("api/v2/files", headers=headers)
    assert response.status_code == 200
    files = response.json()
    file_names = [f["name"] for f in files]
    file_ids = [f["id"] for f in files]
    assert file1["name"] in file_names
    assert file2["name"] in file_names
    assert file1["id"] in file_ids
    assert file2["id"] in file_ids
    assert len(files) == 2

    # Delete one file
    response = await files_client.delete(f"api/v2/files/{file1['id']}", headers=headers)
    assert response.status_code == 200

    # List files again and validate only the other remains
    response = await files_client.get("api/v2/files", headers=headers)
    assert response.status_code == 200
    files = response.json()
    file_names = [f["name"] for f in files]
    file_ids = [f["id"] for f in files]
    assert file1["name"] not in file_names
    assert file1["id"] not in file_ids
    assert file2["name"] in file_names
    assert file2["id"] in file_ids
    assert len(files) == 1