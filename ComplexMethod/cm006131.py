async def test_should_not_persist_in_my_files_when_upload_is_ephemeral(files_client, files_created_api_key):
    """Ephemeral uploads save the file to storage but do NOT create a UserFile DB record.

    This is the expected behavior for chat playground uploads in Desktop,
    where the file must be servable (for chat history) but should not
    appear in the user's 'My Files' list.
    """
    headers = {"x-api-key": files_created_api_key.api_key}

    # Upload with ephemeral=true
    response = await files_client.post(
        "api/v2/files",
        files={"file": ("playground_image.png", b"fake image content")},
        params={"ephemeral": "true"},
        headers=headers,
    )
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"

    upload_response = response.json()
    assert "path" in upload_response

    # The file must NOT appear in the user's file list
    list_response = await files_client.get("api/v2/files", headers=headers)
    assert list_response.status_code == 200
    file_names = [f["name"] for f in list_response.json()]
    assert "playground_image" not in file_names, (
        f"Ephemeral file should not appear in My Files, but found: {file_names}"
    )

    # The file is saved in storage and the response includes a valid path
    file_path = upload_response["path"]
    assert file_path, "Ephemeral upload should return a non-empty path"
    # Path format: {user_id}/{stored_file_name}
    parts = file_path.split("/")
    assert len(parts) == 2, f"Expected path format 'user_id/filename', got: {file_path}"