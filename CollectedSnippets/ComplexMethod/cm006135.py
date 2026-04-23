async def test_mcp_servers_file_replacement(files_client, files_created_api_key, files_active_user):
    """Test that _mcp_servers file gets replaced instead of creating unique names."""
    headers = {"x-api-key": files_created_api_key.api_key}

    mcp_file_ext = await get_mcp_file(files_active_user, extension=True)
    mcp_file = await get_mcp_file(files_active_user)

    # Upload first _mcp_servers file
    response1 = await files_client.post(
        "api/v2/files",
        files={"file": (mcp_file_ext, b'{"servers": ["server1"]}')},
        headers=headers,
    )
    assert response1.status_code == 201
    file1 = response1.json()
    assert file1["name"] == mcp_file

    # Upload second _mcp_servers file - should replace the first one
    response2 = await files_client.post(
        "api/v2/files",
        files={"file": (mcp_file_ext, b'{"servers": ["server2"]}')},
        headers=headers,
    )
    assert response2.status_code == 201
    file2 = response2.json()
    assert file2["name"] == mcp_file

    # Note: _mcp_servers files are filtered out from the regular file list
    # This is expected behavior since they're managed separately
    response = await files_client.get("api/v2/files", headers=headers)
    assert response.status_code == 200
    files = response.json()
    mcp_files = [f for f in files if f["name"] == mcp_file]
    assert len(mcp_files) == 0  # MCP servers files are filtered out from regular list

    # Verify the second file can be downloaded with the updated content
    download2 = await files_client.get(f"api/v2/files/{file2['id']}", headers=headers)
    assert download2.status_code == 200
    assert download2.content == b'{"servers": ["server2"]}'

    # Verify the first file no longer exists (should return 404)
    download1 = await files_client.get(f"api/v2/files/{file1['id']}", headers=headers)
    assert download1.status_code == 404

    # Verify the file IDs are different (new file replaced old one)
    assert file1["id"] != file2["id"]