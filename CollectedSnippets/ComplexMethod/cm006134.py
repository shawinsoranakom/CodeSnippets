async def test_upload_files_without_extension_creates_unique_names(files_client, files_created_api_key):
    """Test that uploading files without extensions also creates unique filenames."""
    headers = {"x-api-key": files_created_api_key.api_key}

    # Upload first file without extension
    response1 = await files_client.post(
        "api/v2/files",
        files={"file": ("noextension", b"content1")},
        headers=headers,
    )
    assert response1.status_code == 201
    file1 = response1.json()
    assert file1["name"] == "noextension"

    # Upload second file with same name
    response2 = await files_client.post(
        "api/v2/files",
        files={"file": ("noextension", b"content2")},
        headers=headers,
    )
    assert response2.status_code == 201
    file2 = response2.json()
    assert file2["name"] == "noextension (1)"

    # Verify both files can be downloaded
    download1 = await files_client.get(f"api/v2/files/{file1['id']}", headers=headers)
    assert download1.status_code == 200
    assert download1.content == b"content1"

    download2 = await files_client.get(f"api/v2/files/{file2['id']}", headers=headers)
    assert download2.status_code == 200
    assert download2.content == b"content2"