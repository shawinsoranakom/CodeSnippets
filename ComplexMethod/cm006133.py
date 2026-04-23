async def test_upload_files_with_same_name_creates_unique_names(files_client, files_created_api_key):
    """Test that uploading files with the same name creates unique filenames."""
    headers = {"x-api-key": files_created_api_key.api_key}

    # Upload first file
    response1 = await files_client.post(
        "api/v2/files",
        files={"file": ("duplicate.txt", b"content1")},
        headers=headers,
    )
    assert response1.status_code == 201
    file1 = response1.json()
    assert file1["name"] == "duplicate"

    # Upload second file with same name
    response2 = await files_client.post(
        "api/v2/files",
        files={"file": ("duplicate.txt", b"content2")},
        headers=headers,
    )
    assert response2.status_code == 201
    file2 = response2.json()
    assert file2["name"] == "duplicate (1)"

    # Upload third file with same name
    response3 = await files_client.post(
        "api/v2/files",
        files={"file": ("duplicate.txt", b"content3")},
        headers=headers,
    )
    assert response3.status_code == 201
    file3 = response3.json()
    assert file3["name"] == "duplicate (2)"

    # Verify all files can be downloaded with their unique content
    download1 = await files_client.get(f"api/v2/files/{file1['id']}", headers=headers)
    assert download1.status_code == 200
    assert download1.content == b"content1"

    download2 = await files_client.get(f"api/v2/files/{file2['id']}", headers=headers)
    assert download2.status_code == 200
    assert download2.content == b"content2"

    download3 = await files_client.get(f"api/v2/files/{file3['id']}", headers=headers)
    assert download3.status_code == 200
    assert download3.content == b"content3"

    # List files and verify all three are present with unique names
    response = await files_client.get("api/v2/files", headers=headers)
    assert response.status_code == 200
    files = response.json()
    file_names = [f["name"] for f in files]
    assert "duplicate" in file_names
    assert "duplicate (1)" in file_names
    assert "duplicate (2)" in file_names
    assert len(files) == 3